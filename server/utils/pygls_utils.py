"""Utilities to simplify some operations with pygls.
"""

from typing import Optional
from pygls.types import Position, Range
from pygls.workspace import Document

from ..types import WordLocation


def get_word_at_position(
    document: Document, position: Position
) -> Optional[WordLocation]:
    """Gets the word at the given document position.

    The resulting WordLocation contains the actual text of the word
    and the start and end position in the document.
    If there is no word in the given position, None will be returned.
    """
    word = document.word_at_position(position)
    word_len = len(word)

    if word_len == 0:
        return None

    line: str = document.lines[position.line]
    start = position.character - word_len

    if start < 0:
        start = 0

    begin = line.find(word, start)
    end = begin + word_len

    return WordLocation(
        word,
        Range(
            start=Position(line=position.line, character=begin),
            end=Position(line=position.line, character=end),
        ),
    )
