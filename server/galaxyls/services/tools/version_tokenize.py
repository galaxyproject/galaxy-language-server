"""Code Action: factor a tool's literal version into @TOOL_VERSION@/@VERSION_SUFFIX@.

This binds the offset-returning version-tokenization planner from ``galaxy_tool_source``
(``tokenize_version_plan``, which returns minimal ``(start, end, replacement)`` edits over
the original source plus, in separate-file mode, the full content of a new ``macros.xml``)
to an LSP ``textDocument/codeAction``. It is the version-tokenization sibling of the
parameter-rename binding (``rename.py``): the engine owns the soundness, kept only when the
tokenization macro-expands byte-identically to the original (the IUC "Tool versions"
practice), so this layer is offset/``Range`` conversion plus ``WorkspaceEdit`` assembly.

Two actions are offered when the cursor is on the ``<tool …>`` start tag of a tool the
engine reports as a candidate (a literal ``version="<base>+galaxy<suffix>"`` whose base
matches a package ``<requirement>``):

- **Define version tokens** — define the two ``<token>``s in an inline ``<macros>`` block
  (a single-document ``WorkspaceEdit`` of minimal ``TextEdit``s).
- **Extract version tokens to macros.xml** — define them in a new imported ``macros.xml``
  (a multi-document ``WorkspaceEdit``: a ``CreateFile`` resource operation plus the new
  file's content, plus the ``<import>`` and token references in the tool). This reuses the
  ``CreateFile`` shape of the extract-to-macros-file refactor (``refactor.py``).

The document's filesystem path is passed to the planner as ``source_path`` so its
expansion-equality gate can resolve the tool's own ``<import>``ed macro files; a tool with
unresolved imports simply yields no action (the planner fails closed).
"""

from pathlib import Path

from galaxy_tool_source.version_tokens import VersionTokenPlan, tokenize_version_plan
from lsprotocol.types import (
    CodeAction,
    CodeActionKind,
    CodeActionParams,
    CreateFile,
    OptionalVersionedTextDocumentIdentifier,
    Position,
    Range,
    ResourceOperationKind,
    TextDocumentEdit,
    TextEdit,
    WorkspaceEdit,
)
from pygls.uris import to_fs_path
from pygls.workspace import TextDocument

from galaxyls.services.tools.constants import TOOL
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.utils import convert_document_offsets_to_range

DEFAULT_MACROS_FILENAME = "macros.xml"


class VersionTokenizeService:
    """Code Actions that factor a literal tool version into the IUC version tokens."""

    def create_version_tokenize_actions(
        self, xml_document: XmlDocument, params: CodeActionParams
    ) -> list[CodeAction]:
        """The version-tokenize Code Actions available at ``params.range``, if any."""
        if not xml_document.is_tool_file:
            return []
        tool = GalaxyToolXmlDocument.from_xml_document(xml_document)
        tool_element = tool.find_element(TOOL)
        if tool_element is None:
            return []
        document = xml_document.document
        tag_range = convert_document_offsets_to_range(
            document,
            tool_element.start_tag_open_offset,
            tool_element.start_tag_close_offset,
        )
        if not (tag_range.start.line <= params.range.start.line <= tag_range.end.line):
            return []
        source_path = to_fs_path(document.uri)
        path = Path(source_path) if source_path is not None else None
        inline = tokenize_version_plan(document.source, source_path=path)
        if inline.bailed:
            return []
        actions = [self._inline_action(document, inline)]
        separate = tokenize_version_plan(
            document.source, source_path=path, macros_file=DEFAULT_MACROS_FILENAME
        )
        if not separate.bailed and separate.new_file is not None:
            extract = self._separate_file_action(document, separate)
            if extract is not None:
                actions.append(extract)
        return actions

    def _text_edits(self, document: TextDocument, plan: VersionTokenPlan) -> list[TextEdit]:
        """The plan's offset edits as document-ordered, non-overlapping ``TextEdit``s."""
        edits = [
            TextEdit(
                range=convert_document_offsets_to_range(document, edit.start, edit.end),
                new_text=edit.replacement,
            )
            for edit in sorted(plan.edits, key=lambda edit: edit.start)
        ]
        return edits

    def _inline_action(self, document: TextDocument, plan: VersionTokenPlan) -> CodeAction:
        return CodeAction(
            title="Define @TOOL_VERSION@/@VERSION_SUFFIX@ version tokens",
            kind=CodeActionKind.RefactorRewrite,
            edit=WorkspaceEdit(changes={document.uri: self._text_edits(document, plan)}),
        )

    def _separate_file_action(
        self, document: TextDocument, plan: VersionTokenPlan
    ) -> CodeAction | None:
        assert plan.new_file is not None  # the caller checked it
        fs_path = to_fs_path(document.uri)
        if fs_path is None or not Path(fs_path).is_absolute():
            return None  # cannot resolve a sibling file URI for the new macros file
        new_file_uri = (Path(fs_path).parent / plan.new_file.path).as_uri()
        new_doc_position = Position(line=0, character=0)
        document_changes: list[CreateFile | TextDocumentEdit] = [
            CreateFile(uri=new_file_uri, kind=ResourceOperationKind.Create),
            TextDocumentEdit(
                text_document=OptionalVersionedTextDocumentIdentifier(
                    uri=new_file_uri, version=0
                ),
                edits=[
                    TextEdit(
                        range=Range(start=new_doc_position, end=new_doc_position),
                        new_text=plan.new_file.content,
                    )
                ],
            ),
            TextDocumentEdit(
                text_document=OptionalVersionedTextDocumentIdentifier(
                    uri=document.uri, version=document.version
                ),
                edits=self._text_edits(document, plan),
            ),
        ]
        return CodeAction(
            title=f"Extract version tokens to {plan.new_file.path}",
            kind=CodeActionKind.RefactorExtract,
            edit=WorkspaceEdit(document_changes=document_changes),
        )
