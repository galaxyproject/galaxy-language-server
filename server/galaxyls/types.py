"""This module contains shared types across all modules.
"""

from typing import List, Optional
from pydantic.main import BaseModel
from pygls.lsp.types import Position, Range


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

    def __init__(
        self,
        snippet: str,
        insert_position: Position,
        replace_range: Optional[Range] = None,
        error_message: Optional[str] = None,
    ):
        self.snippet = snippet
        self.position = insert_position
        self.replace_range = replace_range
        self.error_message = error_message

    @staticmethod
    def as_error(error_message: str) -> "GeneratedSnippetResult":
        """Returns a GeneratedSnippetResult with empty values and the given error message.

        The error message should be displayed or logged by the client."""
        return GeneratedSnippetResult("", Position(line=0, character=0), error_message=error_message)


class ReplaceTextRangeResult:
    """Represents a position range in the document that should be replaced with some text."""

    def __init__(self, replace_range: Range, text: str) -> None:
        self.replace_range = replace_range
        self.text = text


class TestInfoResult:
    """Contains information about a particular test case."""

    def __init__(self, tool_id: str, test_id: str, file: str, line: int, skipped: bool = False) -> None:
        self.id = f"{tool_id}:{test_id}"
        self.label = f"{tool_id}:Test #{test_id}"
        self.file = file
        self.line = line
        self.skipped = skipped
        self.description: Optional[str] = None
        self.tooltip: Optional[str] = None
        self.debuggable: bool = False
        self.errored: bool = False
        self.message: Optional[str] = None


class TestSuiteInfoResult:
    """Contains information about all the tests for a tool wrapper."""

    def __init__(self, tool_id: str, file: str, children: List[TestInfoResult] = None) -> None:
        self.id = tool_id
        self.label = f"{tool_id} tests"
        self.file = file
        self.children = children
        self.line: int = 0
        self.debuggable: bool = False
        self.description: Optional[str] = None
        self.tooltip: Optional[str] = None

        self.errored: bool = False
        self.message: Optional[str] = None


class GeneratedExpandedDocument(BaseModel):
    """Represents a tool document with all the macros expanded."""

    content: Optional[str]
    error_message: Optional[str]
