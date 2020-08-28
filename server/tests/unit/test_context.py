import pytest

from ...services.context import XmlContextService

from pygls.workspace import Document, Position

# The content starts at line 1 for convenience
FAKE_CONTENT = """
<tool id="test">
    <description/>
    <test value="0"/>
</tool>'
"""
FAKE_DOC_URI = "file://fake_doc.xml"
FAKE_DOCUMENT = Document(FAKE_DOC_URI, FAKE_CONTENT)


test_data_for_current_tag = [
    (FAKE_DOCUMENT, Position(line=1, character=4), "tool"),
    (FAKE_DOCUMENT, Position(line=1, character=8), "tool"),
    (FAKE_DOCUMENT, Position(line=2, character=0), "tool"),
    (FAKE_DOCUMENT, Position(line=3, character=0), "tool"),
    (FAKE_DOCUMENT, Position(line=3, character=21), "tool"),
    (FAKE_DOCUMENT, Position(line=4, character=0), "tool"),
    (FAKE_DOCUMENT, Position(line=2, character=5), "description"),
    (FAKE_DOCUMENT, Position(line=2, character=17), "description"),
    (FAKE_DOCUMENT, Position(line=3, character=5), "test"),
    (FAKE_DOCUMENT, Position(line=3, character=12), "test"),
    (FAKE_DOCUMENT, Position(line=3, character=17), "test"),
]


@pytest.mark.parametrize(
    "document,position,expected", test_data_for_current_tag
)
def test_get_current_tag_at_position_is_expected(
    document: Document, position: Position, expected: str
):
    offset = document.offset_at_position(position)

    actual = XmlContextService.find_current_tag(document.source, offset)

    assert actual == expected


def test_get_current_tag_returns_none_when_empty_document():
    xml_content = ""
    offset = 0

    actual = XmlContextService.find_current_tag(xml_content, offset)

    assert actual is None
