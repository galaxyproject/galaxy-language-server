from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    List,
    Optional,
    Tuple,
    Union,
    cast,
)

from lsprotocol.types import (
    Position,
    Range,
)

from galaxyls.services.tools.constants import (
    DASH,
    UNDERSCORE,
)
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.tools.generators import DisplayableException
from galaxyls.types import GeneratedSnippetResult, ReplaceTextRangeResult, WorkspaceEditResult


class WorkspaceEditsGenerator(ABC):
    """This class is used to generate workspace edits using the information of the tool document."""

    def __init__(self, tool_document: GalaxyToolXmlDocument, tabSize: int = 4) -> None:
        self.tool_document = tool_document
        self.expanded_document = tool_document.get_expanded_tool_document()
        self.tabstop_count: int = 0
        self.indent_spaces: str = " " * tabSize
        super().__init__()

    def generate_workspace_edit(self) -> WorkspaceEditResult:
        """Generates a workspace edit using this generator."""
        try:
            edits = self._build_workspace_edits()
            return WorkspaceEditResult(edits)
        except DisplayableException as e:
            return WorkspaceEditResult.as_error(str(e))

    @abstractmethod
    def _build_workspace_edits(self) -> List[ReplaceTextRangeResult]:
        """This abstract function should return a list of ReplaceTextRangeResult
        with the generated workspace edits.
        """
        pass


class SnippetGenerator(ABC):
    """This abstract class defines an XML code snippet generator that can create TextMate
    snippets using the information of the tool document."""

    def __init__(self, tool_document: GalaxyToolXmlDocument, tabSize: int = 4) -> None:
        self.tool_document = tool_document
        self.expanded_document = tool_document.get_expanded_tool_document()
        self.tabstop_count: int = 0
        self.indent_spaces: str = " " * tabSize
        super().__init__()

    def generate_snippet(self) -> GeneratedSnippetResult:
        """Generates a code snippet using this generator."""
        result, is_error = self._build_snippet()
        if is_error:
            return GeneratedSnippetResult.as_error(result)
        insert_position = self._find_snippet_insert_position()
        if type(insert_position) is Range:
            insert_position = cast(Range, insert_position)
            return GeneratedSnippetResult(result, insert_position.start, insert_position)
        insert_position = cast(Position, insert_position)
        return GeneratedSnippetResult(result, insert_position)

    @abstractmethod
    def _build_snippet(self) -> Tuple[str, bool]:
        """This abstract function should return a tuple with the generated snippet text in TextMate format or
        an error message if the snippet can't be generated.

        The second value of the tuple is a bool indicating if there was an error."""
        pass

    @abstractmethod
    def _find_snippet_insert_position(self) -> Union[Position, Range]:
        """This abstract function should find the proper position inside the document where the
        snippet will be inserted."""
        pass

    def _get_next_tabstop(self) -> str:
        """Increments the tabstop count and returns the current tabstop
        in TextMate format.

        Returns:
            str: The current tabstop for the code snippet.
        """
        self.tabstop_count += 1
        return f"${self.tabstop_count}"

    def _get_next_tabstop_with_placeholder(self, placeholder: str) -> str:
        """Returns the current tabstop with a placeholder text.

        Args:
            placeholder (str): The placeholder text that will appear on this tabstop.

        Returns:
            str: The current tabstop with the placeholder text.
        """
        self.tabstop_count += 1
        return f"${{{self.tabstop_count}:{placeholder}}}"

    def _get_next_tabstop_with_options(self, options: List[str], default_option: Optional[str] = None) -> str:
        """Gets the current tabstop with a list of possible options.

        If the list is empty, a normal tabstop is returned.

        Args:
            options (List[str]): The list of options that can be selected in this tabstop.

        Returns:
            str: The current tabstop with all the available options.
        """
        if options:
            if default_option:
                options.remove(default_option)
                options.insert(0, default_option)
            self.tabstop_count += 1
            return f"${{{self.tabstop_count}|{','.join(options)}|}}"
        return self._get_next_tabstop()

    def _extract_name_from_argument(self, argument: str) -> str:
        return argument.lstrip(DASH).replace(DASH, UNDERSCORE)
