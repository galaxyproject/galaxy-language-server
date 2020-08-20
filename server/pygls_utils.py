
"""
Utilities to simplify some operations with pygls.
"""

from typing import Optional
from pygls.types import Position, Range
from pygls.workspace import Document


class WordLocation:
    def __init__(self, word: str, position_range: Range):
        self.text = word
        self.position_range = position_range


def get_word_at_position(document: Document,
                         position: Position) -> Optional[WordLocation]:
    """Gets the WordLocation at the given document position."""
    word = document.word_at_position(position)
    word_len = len(word)

    if word_len == 0:
        return None

    line: str = document.lines[position.line]
    start = position.character-word_len

    if start < 0:
        start = 0

    begin = line.find(word, start)
    end = begin + word_len

    return WordLocation(word, Range(
        start=Position(line=position.line, character=begin),
        end=Position(line=position.line, character=end),
    ))
