"""Unit tests for the pygls utils.
"""

import pytest

from pygls.workspace import Document, Position
from pygls.types import Range

from ...utils.pygls_utils import WordLocation, get_word_at_position

# The content starts at line 1 for convenience
FAKE_CONTENT = """
<tool id="test">
    <description/>
    <test value="0"/>
</tool>'
"""
FAKE_DOC_URI = "file://fake_doc.xml"
FAKE_DOCUMENT = Document(FAKE_DOC_URI, FAKE_CONTENT)


testdata_for_word_location = [
    (FAKE_DOCUMENT, Position(0, 0), None),  # Line 0 is empty
    (
        FAKE_DOCUMENT,
        Position(1, 3),
        WordLocation(
            "tool", Range(start=Position(line=1, character=1), end=Position(line=1, character=5),),
        ),
    ),
    (
        FAKE_DOCUMENT,
        Position(1, 7),
        WordLocation(
            "id", Range(start=Position(line=1, character=6), end=Position(line=1, character=8),),
        ),
    ),
    (
        FAKE_DOCUMENT,
        Position(2, 5),
        WordLocation(
            "description",
            Range(start=Position(line=2, character=5), end=Position(line=2, character=16),),
        ),
    ),
    (FAKE_DOCUMENT, Position(2, 17), None),
    (FAKE_DOCUMENT, Position(3, 2), None),
    (
        FAKE_DOCUMENT,
        Position(4, 2),
        WordLocation(
            "tool", Range(start=Position(line=4, character=2), end=Position(line=4, character=6),),
        ),
    ),
]


@pytest.mark.parametrize("document,position,expected", testdata_for_word_location)
def test_get_word_at_position(document: Document, position: Position, expected: WordLocation):
    actual = get_word_at_position(document, position)

    assert actual == expected


testdata_for_word_location_equality = [
    (
        WordLocation("test", Range(Position(), Position())),
        WordLocation("test", Range(Position(), Position())),
        True,
    ),
    (
        WordLocation("test", Range(Position(), Position())),
        WordLocation("test2", Range(Position(), Position())),
        False,
    ),
    (
        WordLocation("test", Range(Position(), Position())),
        WordLocation("test", Range(Position(1, 0), Position())),
        False,
    ),
]


@pytest.mark.parametrize("word,other_word,expected", testdata_for_word_location_equality)
def test_word_location_equality(word: WordLocation, other_word: WordLocation, expected: bool):
    actual = word == other_word
    assert actual == expected


def test_word_location_equals_not_implemented_for_other_types():
    equals = WordLocation("test", Range(Position(), Position())).__eq__("other type")
    assert equals == NotImplemented
