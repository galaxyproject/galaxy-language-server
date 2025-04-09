"""This module contains shared types across all modules."""

from typing import (
    Any,
    List,
    Optional,
)

import attrs
from lsprotocol.types import (
    Position,
    Range,
)

CommandParameters = List[Any]


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


class WorkspaceEditResult:
    """Contains the workspace edit result for a requested operation."""

    def __init__(self, edits: List[ReplaceTextRangeResult], error_message: Optional[str] = None) -> None:
        self.edits = edits
        self.error_message = error_message

    @staticmethod
    def as_error(error_message: str) -> "WorkspaceEditResult":
        """Returns a RequestedWorkspaceEditResult with empty values and the given error message.

        The error message should be displayed or logged by the client."""
        return WorkspaceEditResult([], error_message=error_message)


class TestInfoResult:
    """Contains information about a particular test case."""

    def __init__(self, tool_id: str, test_id: str, uri: str, range: Range, skipped: bool = False) -> None:
        self.id = f"{tool_id}:{test_id}"
        self.label = f"{tool_id}:Test #{test_id}"
        self.uri = uri
        self.range = range


class TestSuiteInfoResult:
    """Contains information about all the tests for a tool wrapper."""

    def __init__(self, tool_id: str, uri: str, range: Range, children: Optional[List[TestInfoResult]] = None) -> None:
        self.id = tool_id
        self.label = f"{tool_id} tests"
        self.uri = uri
        self.range = range
        self.children = children


@attrs.define
class GeneratedExpandedDocument:
    """Represents a tool document with all the macros expanded."""

    content: Optional[str] = attrs.field(default=None)
    error_message: Optional[str] = attrs.field(default=None, alias="errorMessage")


class ParamReferencesResult:
    """Contains information about the references to a parameter in the document."""

    def __init__(
        self,
        references: List[str],
    ) -> None:
        self.references = references
