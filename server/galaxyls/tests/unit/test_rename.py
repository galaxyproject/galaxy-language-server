"""Tests for the tool-parameter Rename Symbol / Find References feature (rename.py)."""

import pytest

pytest.importorskip("galaxy_tool_xml", reason="the optional rename engine is not installed")

from lsprotocol.types import Position, WorkspaceEdit  # noqa: E402
from pygls.exceptions import JsonRpcInvalidParams  # noqa: E402
from pygls.workspace import TextDocument  # noqa: E402

from galaxyls.services.tools.rename import RenameService  # noqa: E402
from galaxyls.tests.unit.utils import TestUtils  # noqa: E402

# The cursor marker placed inside a source string; removed before parsing.
MARK = "^"


def _document_and_position(source_with_mark: str) -> tuple[TextDocument, Position]:
    """A (TextDocument, Position) pair from a source string with a single MARK cursor."""
    position, source = TestUtils.extract_mark_from_source(MARK, source_with_mark)
    return TestUtils.to_document(source), position


def _apply_workspace_edit(document: TextDocument, workspace_edit: WorkspaceEdit) -> str:
    """Apply a single-document WorkspaceEdit's TextEdits to the source, highest offset first."""
    assert workspace_edit.changes is not None
    edits = workspace_edit.changes[document.uri]
    spans = [
        (document.offset_at_position(edit.range.start), document.offset_at_position(edit.range.end), edit.new_text)
        for edit in edits
    ]
    result = document.source
    for start, end, new_text in sorted(spans, reverse=True):
        result = result[:start] + new_text + result[end:]
    return result


# --- prepareRename --------------------------------------------------------------


def test_prepare_rename_accepts_on_command_reference() -> None:
    document, position = _document_and_position(
        "<tool><inputs><param name='old'/></inputs><command>run $o^ld -o out</command></tool>"
    )
    rename_range = RenameService().prepare_rename(document, position)
    assert rename_range is not None
    start = document.offset_at_position(rename_range.start)
    end = document.offset_at_position(rename_range.end)
    assert document.source[start:end] == "old"


def test_prepare_rename_accepts_on_definition() -> None:
    document, position = _document_and_position(
        "<tool><inputs><param name='o^ld'/></inputs><command>run $old</command></tool>"
    )
    assert RenameService().prepare_rename(document, position) is not None


@pytest.mark.parametrize(
    "source_with_mark",
    [
        # Inside a #raw block: a defined param, but this occurrence is not a live reference.
        "<tool><inputs><param name='old'/></inputs>"
        "<command>#raw\nrun $o^ld\n#end raw\nrun $old</command></tool>",
        # Inside a ## comment.
        "<tool><inputs><param name='old'/></inputs>"
        "<command>## mentions $o^ld\nrun $old</command></tool>",
        # A shell variable, not a defined tool parameter.
        "<tool><command>echo ${SHELL_^VAR} $old</command></tool>",
        # Not on a word at all (whitespace).
        "<tool><inputs><param name='old'/></inputs><command>run $old ^ -o out</command></tool>",
    ],
)
def test_prepare_rename_rejects(source_with_mark: str) -> None:
    document, position = _document_and_position(source_with_mark)
    assert RenameService().prepare_rename(document, position) is None


# --- rename ---------------------------------------------------------------------


def test_rename_rewrites_definition_and_references() -> None:
    document, position = _document_and_position(
        "<tool><inputs><param name='old'/></inputs>"
        "<command>run $o^ld $old -o out</command>"
        "<outputs><data name='o' label='${old}.txt'/></outputs></tool>"
    )
    edit = RenameService().rename(document, position, "renamed")
    result = _apply_workspace_edit(document, edit)
    assert "name='renamed'" in result
    assert "$renamed $renamed" in result
    assert "${renamed}.txt" in result
    assert "old" not in result.replace("name='o'", "")  # no stray old (the data name='o' is unrelated)


def test_rename_through_multiline_tag_and_entities() -> None:
    document, position = _document_and_position(
        "<tool><inputs>\n"
        "  <param name='old'\n"
        "         type='data'/>\n"
        "</inputs><command>echo a &amp;&amp; run $o^ld</command></tool>"
    )
    edit = RenameService().rename(document, position, "aligned")
    result = _apply_workspace_edit(document, edit)
    assert "name='aligned'" in result
    assert "&amp;&amp; run $aligned" in result  # entities preserved, only the token changed


def test_rename_bails_with_message_on_filter_bare_ref() -> None:
    document, position = _document_and_position(
        "<tool><inputs><param name='old'/></inputs><command>run $o^ld</command>"
        "<outputs><data name='out'><filter>old == 'x'</filter></data></outputs></tool>"
    )
    with pytest.raises(JsonRpcInvalidParams) as excinfo:
        RenameService().rename(document, position, "renamed")
    assert "filter" in str(excinfo.value).lower()


def test_rename_bails_with_message_on_invalid_new_name() -> None:
    document, position = _document_and_position(
        "<tool><inputs><param name='old'/></inputs><command>run $o^ld</command></tool>"
    )
    with pytest.raises(JsonRpcInvalidParams) as excinfo:
        RenameService().rename(document, position, "not a valid name")
    assert "not a valid name" in str(excinfo.value)


def test_rename_off_word_raises() -> None:
    document, position = _document_and_position("<tool><command>run $old ^ end</command></tool>")
    with pytest.raises(JsonRpcInvalidParams):
        RenameService().rename(document, position, "renamed")


# --- references -----------------------------------------------------------------


def test_find_references_returns_all_occurrences() -> None:
    document, position = _document_and_position(
        "<tool><inputs><param name='old'/></inputs>"
        "<command>run $o^ld $old</command></tool>"
    )
    locations = RenameService().find_references(document, position)
    assert locations is not None
    # definition name + two command references
    assert len(locations) == 3
    for location in locations:
        assert location.uri == document.uri
        start = document.offset_at_position(location.range.start)
        end = document.offset_at_position(location.range.end)
        assert document.source[start:end] == "old"


def test_find_references_none_off_word() -> None:
    document, position = _document_and_position("<tool><command>run $old^ </command></tool>")
    # cursor just after $old resolves to "old" — to get a true None, sit on whitespace
    document, position = _document_and_position("<tool><command>run $old ^</command></tool>")
    assert RenameService().find_references(document, position) is None
