"""This module contains shared types across all modules.
"""

from pygls.types import Range


class WordLocation:
    """Represents a word in the document with it's text and location.

    The location is a document Range containing the start and
    end position (and the line number) inside de document.
    """

    def __init__(self, word: str, range: Range):
        self.text: str = word
        self.range: Range = range

    def __eq__(self, other):
        if isinstance(other, WordLocation):
            return self.text == other.text and self.range == other.range
        return NotImplemented


class AutoCloseTagResult:
    """Contains the code snippet and the range in the text document that
    will be returned to the client when a tag auto-close is requested.
    """

    def __init__(self, snippet: str, replace_range: Range = None):
        self.snippet = snippet
        self.range = replace_range
