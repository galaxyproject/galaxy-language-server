"""Tests for the version-tokenization Code Action (version_tokenize.py)."""

import pytest

pytest.importorskip(
    "galaxy_tool_source.version_tokens",
    reason="the version-tokenization engine (galaxy-tool-source >= 0.2.0) is not installed",
)

from collections.abc import Sequence  # noqa: E402

from lsprotocol.types import (  # noqa: E402
    CodeAction,
    CodeActionContext,
    CodeActionParams,
    CreateFile,
    Position,
    Range,
    TextDocumentEdit,
    TextDocumentIdentifier,
    TextEdit,
)
from pygls.workspace import TextDocument  # noqa: E402

from galaxyls.services.tools.version_tokenize import VersionTokenizeService  # noqa: E402
from galaxyls.tests.unit.utils import TestUtils  # noqa: E402

_CANDIDATE = (
    '<tool id="m" name="M" version="1.20+galaxy0" profile="24.0">'
    '<requirements><requirement type="package" version="1.20">samtools</requirement>'
    "</requirements>"
    "<command><![CDATA[echo x]]></command>"
    "</tool>"
)


def _actions(source: str, *, line: int = 0, character: int = 6) -> list[CodeAction]:
    xml_document = TestUtils.from_source_to_xml_document(source, uri="file:///tmp/tool.xml")
    cursor = Position(line=line, character=character)
    params = CodeActionParams(
        text_document=TextDocumentIdentifier(uri=xml_document.document.uri),
        range=Range(start=cursor, end=cursor),
        context=CodeActionContext(diagnostics=[]),
    )
    return VersionTokenizeService().create_version_tokenize_actions(xml_document, params)


def _apply_text_edits(document: TextDocument, edits: Sequence[TextEdit]) -> str:
    """Apply TextEdits to the source, highest offset first."""
    spans = [
        (
            document.offset_at_position(edit.range.start),
            document.offset_at_position(edit.range.end),
            edit.new_text,
        )
        for edit in edits
    ]
    result = document.source
    for start, end, new_text in sorted(spans, reverse=True):
        result = result[:start] + new_text + result[end:]
    return result


def test_inline_action_offered_on_candidate() -> None:
    actions = _actions(_CANDIDATE)
    titles = [action.title for action in actions]
    assert any("Define" in title and "version tokens" in title for title in titles)


def test_inline_action_tokenizes_when_applied() -> None:
    document = TestUtils.from_source_to_xml_document(_CANDIDATE, uri="file:///tmp/tool.xml").document
    actions = _actions(_CANDIDATE)
    inline = next(action for action in actions if "Define" in action.title)
    assert inline.edit is not None and inline.edit.changes is not None
    rendered = _apply_text_edits(document, inline.edit.changes[document.uri])
    assert 'version="@TOOL_VERSION@+galaxy@VERSION_SUFFIX@"' in rendered
    assert '<token name="@TOOL_VERSION@">1.20</token>' in rendered
    assert 'version="@TOOL_VERSION@">samtools' in rendered


def test_separate_file_action_creates_macros_file() -> None:
    document = TestUtils.from_source_to_xml_document(_CANDIDATE, uri="file:///tmp/tool.xml").document
    actions = _actions(_CANDIDATE)
    extract = next(action for action in actions if "Extract" in action.title)
    assert extract.edit is not None and extract.edit.document_changes is not None
    changes = extract.edit.document_changes
    create = next(change for change in changes if isinstance(change, CreateFile))
    assert create.uri.endswith("macros.xml")
    # The new file gets the tokens; the tool gets the import + retargeted version.
    new_file_edit = next(
        change
        for change in changes
        if isinstance(change, TextDocumentEdit) and change.text_document.uri == create.uri
    )
    new_file_text = new_file_edit.edits[0]
    assert isinstance(new_file_text, TextEdit)
    assert b'<token name="@TOOL_VERSION@">1.20</token>' in new_file_text.new_text.encode()
    tool_edit = next(
        change
        for change in changes
        if isinstance(change, TextDocumentEdit) and change.text_document.uri == document.uri
    )
    tool_text_edits = [edit for edit in tool_edit.edits if isinstance(edit, TextEdit)]
    rendered = _apply_text_edits(document, tool_text_edits)
    assert "<import>macros.xml</import>" in rendered
    assert 'version="@TOOL_VERSION@+galaxy@VERSION_SUFFIX@"' in rendered


def test_no_action_when_not_a_candidate() -> None:
    plain = _CANDIDATE.replace('version="1.20+galaxy0"', 'version="1.20"')
    assert _actions(plain) == []


def test_no_action_when_cursor_off_the_tool_tag() -> None:
    multiline = (
        '<tool id="m" name="M" version="1.20+galaxy0" profile="24.0">\n'
        '    <requirements><requirement type="package" version="1.20">samtools'
        "</requirement></requirements>\n"
        "    <command><![CDATA[echo x]]></command>\n"
        "</tool>\n"
    )
    # Cursor on the <command> line (2), not the <tool> start tag (line 0).
    assert _actions(multiline, line=2, character=6) == []
