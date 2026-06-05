"""Rename a Galaxy tool parameter (and every reference to it) from the editor.

This binds the offset-returning rename engine from ``galaxy_tool_xml`` (``rename_param_plan``,
which returns minimal ``(start, end, replacement)`` edits over the original source) to the
LSP ``textDocument/prepareRename`` / ``textDocument/rename`` / ``textDocument/references``
requests. The engine owns the semantics — which ``$param`` references are real (through
``#if`` directives, dotted ``$p.metadata`` accesses, output labels, by-name cross-reference
attributes and ``<tests>`` mirrors), refusing to touch a ``$param`` inside ``#raw`` / a ``##``
comment / ``<help>`` prose, and bailing atomically when it cannot prove the rewrite safe —
so this layer is only offset/Range conversion plus a human message for each bail reason.

A parameter is frequently *defined* in the tool but *referenced* inside a macro file it
``<import>``s. The rename therefore spans the **bundle**: it runs the engine over the open
tool document and over each imported macro file, assembling a multi-file ``WorkspaceEdit``
so a reference living only in a macro is not silently left dangling. Macro files are read
through the workspace (honouring unsaved editor buffers) when one is available, else from
disk. The whole rename bails if a macro file references the parameter but cannot be rewritten
safely (the same atomicity the single-tool rename guarantees).

**Caveat — no shared-macro gate.** An imported macro is rewritten whenever the open tool
references the parameter through it, *without* checking whether **other** tools also import
that macro. If the macro is shared, this rename updates the open tool (and the macro) but
leaves the other importers still defining the old name — they would each need the same
rename. The editor shows the full multi-file ``WorkspaceEdit`` to review before applying, so
the macro edit is at least visible; but the *other* importers are not, so a shared-macro
rename can leave them inconsistent. The ``galaxy-tool-refactor`` CLI enforces this across a
repository (``rename-param --repo-root`` skips a shared macro, or ``--across-importers``
renames every importer in lockstep); bringing that cross-tool gate into the editor — via a
workspace-wide importer scan — is future work (see the integration note in the
galaxy-tool-refactor repo, ``docs/upgrade_research/lsp_rename_integration.md``).
"""

from pathlib import Path

from galaxy_tool_xml.cheetah_rename import RenamePlan, rename_param_plan
from galaxy_tool_xml.macros import imported_macro_paths
from lsprotocol.types import (
    Location,
    Position,
    Range,
    TextEdit,
    WorkspaceEdit,
)
from lxml import etree
from pygls.exceptions import JsonRpcInvalidParams
from pygls.uris import from_fs_path, to_fs_path
from pygls.workspace import TextDocument, Workspace

from galaxyls.services.xml.utils import convert_document_offsets_to_range

# Tags under <inputs>/<outputs> whose ``name`` *defines* a parameter/output: a rename is
# only offered for a name defined in THIS document. References to it may live in the tool
# AND in the macro files it ``<import>``s — the rename follows the parameter into those
# macro files too (see ``RenameService._macro_targets``), so the rewrite stays complete.
_INPUT_DEFINITION_TAGS = frozenset({"param", "conditional", "repeat", "section"})
_OUTPUT_DEFINITION_TAGS = frozenset({"data", "collection"})

# An identifier probe used only to drive prepareRename/references: a valid Cheetah/Python
# identifier that no real tool parameter is named, so the plan exercises the same code path
# the actual rename will (we read only its edit spans, never the replacement text).
_RENAME_PROBE = "galaxylsRenameProbe"

# A human message per atomic bail reason the engine can return (see the rename engine's
# module docstring). Shown to the user when a rename cannot proceed.
_BAIL_MESSAGES = {
    "invalid-name": "'{new}' is not a valid parameter name.",
    "no-op": "The new name is the same as the current name.",
    "not-found": "'{old}' is not a renameable tool parameter.",
    "shadowed": "Can't safely rename '{old}': it is shadowed by a Cheetah #set/#for/#def binding.",
    "mixed-content": "Can't safely rename '{old}': its command/configfile mixes text and child elements.",
    "lexer-bail": "Can't safely rename '{old}': a Cheetah section could not be parsed.",
    "filter-bare-ref": "Can't safely rename '{old}': it is referenced by bare name in an output <filter>.",
    "cross-ref-residual": "Can't safely rename '{old}': an unmodeled by-name reference would be left dangling.",
}
_FALLBACK_BAIL_MESSAGE = "Can't compute a precise rename for '{old}' in this document."


def _identifier_at(source: str, offset: int) -> str | None:
    """The Cheetah/Python identifier covering *offset* in *source*, or ``None``.

    Expands over ``[A-Za-z_]\\w*`` around the cursor (``$`` and ``.`` are not word
    characters, so a cursor on ``old`` in ``$cond.old`` yields ``"old"``). Returns ``None``
    when the cursor is not on a word or the run starts with a digit (not an identifier).
    """
    length = len(source)
    if offset < 0 or offset > length:
        return None
    start = offset
    while start > 0 and (source[start - 1].isalnum() or source[start - 1] == "_"):
        start -= 1
    end = offset
    while end < length and (source[end].isalnum() or source[end] == "_"):
        end += 1
    word = source[start:end]
    if not word or not (word[0].isalpha() or word[0] == "_"):
        return None
    return word


def _defined_param_names(source: str) -> set[str]:
    """Names defined by an ``<inputs>``/``<outputs>`` element in *source* (best effort)."""
    parser = etree.XMLParser(recover=True)
    try:
        root = etree.fromstring(source.encode("utf-8"), parser)
    except (etree.XMLSyntaxError, ValueError):
        return set()
    if root is None:
        return set()
    names: set[str] = set()
    for section, tags in (("inputs", _INPUT_DEFINITION_TAGS), ("outputs", _OUTPUT_DEFINITION_TAGS)):
        container = root.find(section)
        if container is None:
            continue
        for element in container.iter():
            if isinstance(element.tag, str) and element.tag in tags:
                name = element.get("name")
                if name:
                    names.add(name)
    return names


def _text_edits(document: TextDocument, plan: RenamePlan) -> list[TextEdit]:
    """Convert a rename plan's offset edits into LSP ``TextEdit``\\ s for *document*."""
    return [
        TextEdit(
            range=convert_document_offsets_to_range(document, edit.start, edit.end),
            new_text=edit.replacement,
        )
        for edit in plan.edits
    ]


def _bail_error(old: str, new: str, reason: str | None) -> JsonRpcInvalidParams:
    """The user-facing error for an atomic rename bail."""
    template = _BAIL_MESSAGES.get(reason or "", _FALLBACK_BAIL_MESSAGE)
    return JsonRpcInvalidParams(message=template.format(old=old, new=new))


class RenameService:
    """Provides parameter rename + find-references over a tool document and its macros."""

    def __init__(self, workspace: Workspace | None = None) -> None:
        """*workspace*, when given, makes imported macro reads honour unsaved buffers."""
        self._workspace = workspace

    def set_workspace(self, workspace: Workspace) -> None:
        """Record the workspace so imported macro files are read buffer-first."""
        self._workspace = workspace

    def _macro_targets(self, document: TextDocument) -> list[TextDocument]:
        """The macro files *document* imports, as ``TextDocument``\\ s (buffer-aware).

        Resolves the tool's transitive ``<import>``s relative to its own location on disk
        (``imported_macro_paths``). Each macro is read through the workspace when one is set
        — so an unsaved editor buffer wins — otherwise from disk. Returns ``[]`` for an
        in-memory document with no filesystem path, or one that imports nothing.
        """
        tool_path = to_fs_path(document.uri)
        if tool_path is None:
            return []
        targets: list[TextDocument] = []
        for macro_path in imported_macro_paths(Path(tool_path)):
            uri = from_fs_path(str(macro_path))
            if uri is None:
                continue
            if self._workspace is not None:
                targets.append(self._workspace.get_text_document(uri))
            else:
                targets.append(TextDocument(uri, macro_path.read_text(encoding="utf-8")))
        return targets

    def prepare_rename(self, document: TextDocument, position: Position) -> Range | None:
        """The renameable range under *position*, or ``None`` to reject the rename.

        Accepts only when the cursor sits on a real occurrence of a *locally defined*
        parameter that the rename can rewrite — which rejects ``#raw`` / ``##`` comments /
        ``${SHELL_VAR}`` / ``<help>`` text, macro-supplied references, and unsafe (bailing)
        renames.
        """
        offset = document.offset_at_position(position)
        name = _identifier_at(document.source, offset)
        if name is None or name not in _defined_param_names(document.source):
            return None
        plan = rename_param_plan(document.source, old=name, new=_RENAME_PROBE)
        if plan.bailed:
            return None
        for edit in plan.edits:
            if edit.start <= offset <= edit.end:
                return convert_document_offsets_to_range(document, edit.start, edit.end)
        return None

    def rename(self, document: TextDocument, position: Position, new_name: str) -> WorkspaceEdit:
        """A minimal ``WorkspaceEdit`` renaming the parameter under *position* to *new_name*.

        Raises ``JsonRpcInvalidParams`` with a human message when the rename cannot proceed
        (an atomic bail, an invalid new name, or the cursor not being on a parameter).
        """
        offset = document.offset_at_position(position)
        name = _identifier_at(document.source, offset)
        if name is None or name not in _defined_param_names(document.source):
            raise JsonRpcInvalidParams(message="Place the cursor on a tool parameter to rename it.")
        plan = rename_param_plan(document.source, old=name, new=new_name)
        if plan.bailed:
            raise _bail_error(name, new_name, plan.reason)
        changes = {document.uri: _text_edits(document, plan)}
        for macro in self._macro_targets(document):
            macro_plan = rename_param_plan(macro.source, old=name, new=new_name)
            if macro_plan.bailed:
                # The macro does not mention the parameter -> nothing to do for it. Any
                # other bail means it references the parameter but cannot be rewritten
                # safely, so the whole (atomic) rename is refused rather than half-applied.
                if macro_plan.reason == "not-found":
                    continue
                raise _bail_error(name, new_name, macro_plan.reason)
            if macro_plan.edits:
                changes[macro.uri] = _text_edits(macro, macro_plan)
        return WorkspaceEdit(changes=changes)

    def find_references(self, document: TextDocument, position: Position) -> list[Location] | None:
        """Every occurrence of the parameter under *position*, across the tool and its macros.

        Returns ``None`` when the cursor is not on a renameable parameter. Reuses the rename
        plan's edit spans — each covers exactly one occurrence of the name in a file. Macro
        files that cannot be rewritten safely are skipped (references are best-effort and
        read-only), unlike ``rename`` which bails the whole operation.
        """
        offset = document.offset_at_position(position)
        name = _identifier_at(document.source, offset)
        if name is None or name not in _defined_param_names(document.source):
            return None
        plan = rename_param_plan(document.source, old=name, new=f"{name}Ref")
        if plan.bailed:
            return None
        locations = [
            Location(uri=document.uri, range=convert_document_offsets_to_range(document, edit.start, edit.end))
            for edit in plan.edits
        ]
        for macro in self._macro_targets(document):
            macro_plan = rename_param_plan(macro.source, old=name, new=f"{name}Ref")
            if not macro_plan.bailed:
                locations.extend(
                    Location(uri=macro.uri, range=convert_document_offsets_to_range(macro, edit.start, edit.end))
                    for edit in macro_plan.edits
                )
        return locations
