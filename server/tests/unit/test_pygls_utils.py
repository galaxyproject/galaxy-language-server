"""Unit tests for the pygls utils.
"""

import pytest

from ...utils.pygls_utils import WordLocation, get_word_at_position

from pygls.workspace import Document, Position
from pygls.types import Position, Range


def _get_fake_xml_document():
    fake_document_uri = 'file://fake_doc.xml'
    fake_content = '<tool id="test">\n<description/>\n   <test value="0"/>\n</tool>'
    fake_document = Document(fake_document_uri, fake_content)
    return fake_document


testdata = [
    (_get_fake_xml_document(), Position(0, 3),
     WordLocation("tool", Range(
         start=Position(line=0, character=1),
         end=Position(line=0, character=5),
     ))),
    (_get_fake_xml_document(), Position(0, 7),
     WordLocation("id", Range(
         start=Position(line=0, character=6),
         end=Position(line=0, character=8),
     ))),
    (_get_fake_xml_document(), Position(1, 3),
     WordLocation("description", Range(
         start=Position(line=1, character=1),
         end=Position(line=1, character=12),
     ))),
    (_get_fake_xml_document(), Position(1, 13), None),
    (_get_fake_xml_document(), Position(2, 2), None),
    (_get_fake_xml_document(), Position(3, 2),
     WordLocation("tool", Range(
         start=Position(line=3, character=2),
         end=Position(line=3, character=6),
     ))),
]


@pytest.mark.parametrize("document,position,expected", testdata)
def test_get_word_at_position(document: Document, position: Position, expected: WordLocation):
    actual = get_word_at_position(document, position)

    assert actual == expected
