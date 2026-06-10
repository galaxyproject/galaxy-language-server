"""Tests for the tool-parameter Rename Symbol / Find References feature (rename.py)."""

import pytest

pytest.importorskip("galaxy_tool_source", reason="the optional rename engine is not installed")

from pathlib import Path  # noqa: E402

from lsprotocol.types import Position, WorkspaceEdit  # noqa: E402
from pygls.exceptions import JsonRpcInvalidParams  # noqa: E402
from pygls.uris import from_fs_path  # noqa: E402
from pygls.workspace import TextDocument, Workspace  # noqa: E402

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


def test_rename_now_rewrites_a_clean_filter_bare_ref() -> None:
    # The engine's tokenize-based <filter> rewrite (galaxy-tool-source decisions
    # §22, shipped after the original pin) renames an unambiguous bare reference
    # in an output filter instead of bailing — this case used to raise.
    document, position = _document_and_position(
        "<tool><inputs><param name='old'/></inputs><command>run $o^ld</command>"
        "<outputs><data name='out'><filter>old == 'x'</filter></data></outputs></tool>"
    )
    edit = RenameService().rename(document, position, "renamed")
    result = _apply_workspace_edit(document, edit)
    assert "<filter>renamed == 'x'</filter>" in result
    assert "run $renamed" in result


def test_rename_bails_with_message_on_ambiguous_filter_bare_ref() -> None:
    # Still-bailing residual: *old* also appears as a string literal in the
    # filter (a possible cond['old'] sub-parameter key, indistinguishable from a
    # coincidental value), so the engine refuses rather than guess.
    document, position = _document_and_position(
        "<tool><inputs><param name='old'/></inputs><command>run $o^ld</command>"
        "<outputs><data name='out'><filter>old == 'old'</filter></data></outputs></tool>"
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


# --- cross-file: rename / references span imported macro files -------------------
# A parameter is defined in the tool but referenced in an imported macro (the real
# pal2nal shape). The rename must follow it into the macro file, or it silently breaks.

_PAL2NAL_MACROS = (
    "<macros><xml name='command'>"
    "<command><![CDATA[pal2nal '$protein_alignment']]></command></xml></macros>"
)
_PAL2NAL_TOOL = (
    "<tool id='pal2nal'><macros><import>macros.xml</import></macros>"
    "<inputs><param name='protein_^alignment' type='data'/></inputs>"
    "<expand macro='command'/></tool>"
)


def _bundle(tmp_path: Path, tool_with_mark: str, macros_source: str) -> tuple[TextDocument, Position]:
    """Write tool + macros.xml to *tmp_path*; return the tool's (TextDocument, Position)."""
    (tmp_path / "macros.xml").write_text(macros_source, encoding="utf-8")
    position, source = TestUtils.extract_mark_from_source(MARK, tool_with_mark)
    tool_path = tmp_path / "tool.xml"
    tool_path.write_text(source, encoding="utf-8")
    return TextDocument(from_fs_path(str(tool_path)), source), position


def _macro_uri(tmp_path: Path) -> str:
    return from_fs_path(str((tmp_path / "macros.xml").resolve()))


def _apply_for_uri(uri: str, source: str, workspace_edit: WorkspaceEdit) -> str:
    """Apply a WorkspaceEdit's TextEdits for one *uri* to *source*, highest offset first."""
    assert workspace_edit.changes is not None
    document = TextDocument(uri, source)
    spans = [
        (document.offset_at_position(e.range.start), document.offset_at_position(e.range.end), e.new_text)
        for e in workspace_edit.changes.get(uri, [])
    ]
    result = source
    for start, end, new_text in sorted(spans, reverse=True):
        result = result[:start] + new_text + result[end:]
    return result


def test_rename_spans_imported_macro(tmp_path: Path) -> None:
    document, position = _bundle(tmp_path, _PAL2NAL_TOOL, _PAL2NAL_MACROS)
    edit = RenameService().rename(document, position, "aln")
    assert edit.changes is not None
    macro_uri = _macro_uri(tmp_path)
    assert document.uri in edit.changes and macro_uri in edit.changes  # both files edited
    # The tool's definition is renamed...
    tool_result = _apply_for_uri(document.uri, document.source, edit)
    assert "name='aln'" in tool_result
    # ...and the reference in the macro file is renamed too.
    macro_src = (tmp_path / "macros.xml").read_text(encoding="utf-8")
    macro_result = _apply_for_uri(macro_uri, macro_src, edit)
    assert "$aln" in macro_result and "protein_alignment" not in macro_result


def test_rename_unrelated_macro_is_not_edited(tmp_path: Path) -> None:
    macros = "<macros><xml name='reqs'><requirement>x</requirement></xml></macros>"
    tool = (
        "<tool id='t'><macros><import>macros.xml</import></macros>"
        "<inputs><param name='o^ld'/></inputs><command>run $old</command></tool>"
    )
    document, position = _bundle(tmp_path, tool, macros)
    edit = RenameService().rename(document, position, "new")
    assert edit.changes is not None
    assert _macro_uri(tmp_path) not in edit.changes  # the macro never mentions the param
    assert document.uri in edit.changes


def test_rename_bails_when_macro_reference_is_unsafe(tmp_path: Path) -> None:
    # The macro references the param but a #set local shadows it -> the whole rename bails.
    macros = (
        "<macros><xml name='command'><command>"
        "#set $protein_alignment = 1\nrun $protein_alignment</command></xml></macros>"
    )
    document, position = _bundle(tmp_path, _PAL2NAL_TOOL, macros)
    with pytest.raises(JsonRpcInvalidParams) as excinfo:
        RenameService().rename(document, position, "aln")
    assert "shadow" in str(excinfo.value).lower()


def test_find_references_spans_imported_macro(tmp_path: Path) -> None:
    document, position = _bundle(tmp_path, _PAL2NAL_TOOL, _PAL2NAL_MACROS)
    locations = RenameService().find_references(document, position)
    assert locations is not None
    uris = {location.uri for location in locations}
    assert document.uri in uris  # the definition in the tool
    assert _macro_uri(tmp_path) in uris  # the reference in the macro


# --- shared-macro gate (workspace-aware) ----------------------------------------
# When a rename would edit a macro that ANOTHER tool in the workspace imports, the
# editor refuses (the counterpart of the CLI's sole-owned gate) rather than silently
# leave the sibling tool referencing the old name.


def _open_tool(tmp_path: Path, name: str, source_with_mark: str) -> tuple[TextDocument, Position]:
    """Write a marked tool to *name* and return its (TextDocument with a real uri, Position)."""
    position, source = TestUtils.extract_mark_from_source(MARK, source_with_mark)
    path = tmp_path / name
    path.write_text(source, encoding="utf-8")
    return TextDocument(from_fs_path(str(path)), source), position


def test_rename_refuses_shared_macro_in_workspace(tmp_path: Path) -> None:
    (tmp_path / "shared.xml").write_text(_PAL2NAL_MACROS, encoding="utf-8")
    tail = (
        "<macros><import>shared.xml</import></macros>"
        "<inputs><param name='protein_alignment' type='data'/></inputs>"
        "<expand macro='command'/></tool>"
    )
    # b.xml also imports shared.xml -> the macro is shared.
    (tmp_path / "b.xml").write_text("<tool id='b'>" + tail, encoding="utf-8")
    a_marked = (
        "<tool id='a'><macros><import>shared.xml</import></macros>"
        "<inputs><param name='protein_^alignment' type='data'/></inputs>"
        "<expand macro='command'/></tool>"
    )
    document, position = _open_tool(tmp_path, "a.xml", a_marked)
    service = RenameService(Workspace(from_fs_path(str(tmp_path))))
    with pytest.raises(JsonRpcInvalidParams) as excinfo:
        service.rename(document, position, "aln")
    message = str(excinfo.value)
    assert "shared" in message and "b.xml" in message


def test_rename_sole_owned_macro_with_workspace_applies(tmp_path: Path) -> None:
    # Only the open tool imports the macro -> sole-owned -> the gate does not trip.
    (tmp_path / "shared.xml").write_text(_PAL2NAL_MACROS, encoding="utf-8")
    a_marked = (
        "<tool id='a'><macros><import>shared.xml</import></macros>"
        "<inputs><param name='protein_^alignment' type='data'/></inputs>"
        "<expand macro='command'/></tool>"
    )
    document, position = _open_tool(tmp_path, "a.xml", a_marked)
    service = RenameService(Workspace(from_fs_path(str(tmp_path))))
    edit = service.rename(document, position, "aln")
    assert edit.changes is not None
    assert from_fs_path(str((tmp_path / "shared.xml").resolve())) in edit.changes
