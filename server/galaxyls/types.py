"""This module contains shared types across all modules.
"""

from typing import Optional
from pygls.types import Position, Range


class AutoCloseTagResult:
    """Contains the code snippet and the range in the text document that
    will be returned to the client when a tag auto-close is requested.
    """

    def __init__(self, snippet: str, replace_range: Optional[Range] = None):
        self.snippet = snippet
        self.range = replace_range


class GeneratedSnippetResult:
    """Contains the auto-generated code snippet and the position in the text document
    where it should be inserted.

    Optionally, a Range can be provided to insert the snippet replacing the
    text inside the given range.
    """

    def __init__(self, snippet: str, insert_position: Position, replace_range: Optional[Range] = None):
        self.snippet = snippet
        self.position = insert_position
        self.replace_range = replace_range
