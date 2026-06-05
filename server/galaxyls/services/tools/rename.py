"""Rename a Galaxy tool parameter (and every reference to it) from the editor.

This binds the offset-returning rename engine from ``galaxy_tool_xml`` (``rename_param_plan``,
which returns minimal ``(start, end, replacement)`` edits over the original source) to the
LSP ``textDocument/prepareRename`` / ``textDocument/rename`` / ``textDocument/references``
requests. The engine owns the semantics — which ``$param`` references are real (through
``#if`` directives, dotted ``$p.metadata`` accesses, output labels, by-name cross-reference
attributes and ``<tests>`` mirrors), refusing to touch a ``$param`` inside ``#raw`` / a ``##``
comment / ``<help>`` prose, and bailing atomically when it cannot prove the rewrite safe —
so this layer is only offset/Range conversion plus a human message for each bail reason.
"""

from galaxy_tool_xml.cheetah_rename import rename_param_plan
from lsprotocol.types import (
    Location,
    Position,
    Range,
    TextEdit,
    WorkspaceEdit,
)
from lxml import etree
from pygls.exceptions import JsonRpcInvalidParams
from pygls.workspace import TextDocument

from galaxyls.services.xml.utils import convert_document_offsets_to_range

# Tags under <inputs>/<outputs> whose ``name`` *defines* a parameter/output: a rename is
# only offered for a name defined in THIS document, so renaming every local site is complete
# (a ``$x`` that is merely referenced may be supplied by an imported macro — out of scope).
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


class RenameService:
    """Provides parameter rename + find-references over a tool document."""

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
            template = _BAIL_MESSAGES.get(plan.reason or "", _FALLBACK_BAIL_MESSAGE)
            raise JsonRpcInvalidParams(message=template.format(old=name, new=new_name))
        edits = [
            TextEdit(
                range=convert_document_offsets_to_range(document, edit.start, edit.end),
                new_text=edit.replacement,
            )
            for edit in plan.edits
        ]
        return WorkspaceEdit(changes={document.uri: edits})

    def find_references(self, document: TextDocument, position: Position) -> list[Location] | None:
        """Every occurrence of the parameter under *position* (definition + references).

        Returns ``None`` when the cursor is not on a renameable parameter. Reuses the rename
        plan's edit spans — each covers exactly one occurrence of the name in the source.
        """
        offset = document.offset_at_position(position)
        name = _identifier_at(document.source, offset)
        if name is None or name not in _defined_param_names(document.source):
            return None
        plan = rename_param_plan(document.source, old=name, new=f"{name}Ref")
        if plan.bailed:
            return None
        return [
            Location(uri=document.uri, range=convert_document_offsets_to_range(document, edit.start, edit.end))
            for edit in plan.edits
        ]
