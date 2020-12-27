""" This code is based on the Eclipse/Lemminx XML language server implementation:
https://github.com/eclipse/lemminx/tree/master/org.eclipse.lemminx/src/main/java/org/eclipse/lemminx/dom

Only the minimum subset of the XML dialect used by Galaxy tool wrappers is supported.
"""

from typing import Callable, List

from pygls.types import Position, Range
from pygls.workspace import Document

from .constants import NEW_LINE, _LAN, WHITESPACE_CHARS


def convert_document_offset_to_position(document: Document, offset: int) -> Position:
    """Converts the given offset in the document to a line/character based Position.

    Args:
        document (Document): The source document.
        offset (int): The character offset inside the document.

    Returns:
        Position: The resulting Position with line and character offset.
    """
    line = max(document.source.count(NEW_LINE, 0, offset), 0)
    line_offset = max(document.source.rfind(NEW_LINE, 0, offset), 0)
    character = offset - line_offset
    if line > 0:
        character -= 1
    return Position(line, character)


def convert_document_offsets_to_range(document: Document, start_offset: int, end_offset: int) -> Range:
    """Converts the given start and end offset positions in the document to a
    position Range based on line numbers.

    Args:
        start_offset (int): The start offset of the range
        end_offset (int): The end offset of the range

    Returns:
        Range: The resulting Range with the correct line number and character offset
    """
    return Range(
        convert_document_offset_to_position(document, start_offset),
        convert_document_offset_to_position(document, end_offset),
    )


class MultiLineStream:
    """Represents a multi-line stream of characters."""

    def __init__(self, source: str, position: int = 0) -> None:
        self._source = source
        self._position = position
        self._len = len(source)

    def eos(self) -> bool:
        """Indicates that the stream is at the end position."""
        return self._len <= self._position

    def get_source(self) -> str:
        """Gets the source text."""
        return self._source

    def pos(self) -> int:
        """Gets the current stream position."""
        return self._position

    def advance(self, n: int) -> None:
        """Advances the stream given number of positions."""
        self._position += n

    def go_to_end(self) -> None:
        """Sets the stream position to the end of the stream."""
        self._position = self._len

    def peek_char(self, n: int = 0) -> int:
        """Gets the value of the next position in the stream without advancing it."""
        try:
            return ord(self._source[self._position + n])
        except IndexError:
            return -1

    def advance_if_char(self, ch: int) -> bool:
        """If the next character in the stream matches the given character, the stream advances one position."""
        if ch == self.peek_char():
            self._position += 1
            return True
        return False

    def advance_if_chars(self, ch: List[int]) -> bool:
        """If the next characters in the stream matches the given sequence of characters, the stream advances
        the length of the sequence."""
        ch_length = len(ch)
        if self._position + ch_length > self._len:
            return False
        i = 0
        for i in range(ch_length):
            if self._source[self._position + i] != chr(ch[i]):
                return False
        self.advance(i)
        return True

    def advance_until_char(self, ch: int) -> bool:
        """Advances the stream until it founds a character matching the given."""
        while self._position < self._len:
            if ord(self._source[self._position]) == ch:
                return True
            self.advance(1)
        return False

    def advance_until_chars(self, ch: List[int]) -> bool:
        """Advances the stream until it founds a list of character matching the given."""
        ch_length = len(ch)
        while self._position + ch_length <= self._len:
            i = 0
            while i < ch_length and self._source[self._position + i] == chr(ch[i]):
                i += 1
            if i == ch_length:
                return True
            self.advance(i or 1)
        self.go_to_end()
        return False

    def advance_while_char_in(self, list: List[int]) -> int:
        """Advances the stream if the characters are like any of the characters in the given list."""
        pos_now = self._position
        while self._position < self._len and ord(self._source[self._position]) in list:
            self._position += 1
        return self._position - pos_now

    def advance_until_char_or_new_tag(self, ch: int) -> bool:
        """Advances the stream until it finds the given character or the '<' (new tag character)."""
        while self._position < self._len:
            if self.peek_char() in [ch, _LAN]:
                return True
            self.advance(1)
        return False

    def advance_until_chars_or_new_tag(self, ch: List[int]) -> bool:
        """Advances the stream until it finds the given sequence of characters or the '<' (new tag character)."""
        ch_length = len(ch)
        while self._position + ch_length <= self._len:
            i = 0
            if self.peek_char() == _LAN:
                return True
            while i < ch_length and self._source[self._position + i] == chr(ch[i]):
                i += 1
            if i == ch_length:
                return True
            self.advance(i or 1)
        self.go_to_end()
        return False

    def advance_while_char(self, predicate: Callable[[str], bool]) -> int:
        """Advances the stream while the given condition is True."""
        pos_now = self._position
        while self._position < self._len and predicate(self._source[self._position]):
            self._position += 1
        return self._position - pos_now

    def skip_whitespace(self) -> bool:
        """Advances the stream while any kind of white space character is found."""
        n = self.advance_while_char_in(WHITESPACE_CHARS)
        return n > 0
