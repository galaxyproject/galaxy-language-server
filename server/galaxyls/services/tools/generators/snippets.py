from abc import ABC, abstractmethod
from typing import List, Optional, Union, cast

from galaxy.util import xml_macros
from galaxyls.services.tools.constants import DASH, UNDERSCORE
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.types import GeneratedSnippetResult
from lxml import etree
from pygls.types import Position, Range
from pygls.workspace import Document


class SnippetGenerator(ABC):
    """This abstract class defines an XML code snippet generator that can create TextMate
    snippets using the information of the tool document."""

    def __init__(self, tool_document: GalaxyToolXmlDocument, tabSize: int = 4) -> None:
        self.tool_document: GalaxyToolXmlDocument = tool_document
        self.expanded_document: GalaxyToolXmlDocument = self._get_expanded_tool_document(tool_document)
        self.tabstop_count: int = 0
        self.indent_spaces: str = " " * tabSize
        super().__init__()

    def generate_snippet(self) -> Optional[GeneratedSnippetResult]:
        """Generates a code snippet using this generator."""
        snippet = self._build_snippet()
        if snippet:
            insert_position = self._find_snippet_insert_position()
            if type(insert_position) == Range:
                insert_position = cast(Range, insert_position)
                return GeneratedSnippetResult(snippet, insert_position.start, insert_position)
            insert_position = cast(Position, insert_position)
            return GeneratedSnippetResult(snippet, insert_position)
        return None

    @abstractmethod
    def _build_snippet(self) -> Optional[str]:
        """This abstract function should return the generated snippet in TextMate format or None
        if the snippet can't be generated."""
        pass

    @abstractmethod
    def _find_snippet_insert_position(self) -> Union[Position, Range]:
        """This abstract function should find the proper position inside the document where the
        snippet will be inserted."""
        pass

    def _get_expanded_tool_document(self, tool_document: GalaxyToolXmlDocument) -> GalaxyToolXmlDocument:
        """If the given tool document uses macros, a new tool document with the expanded macros is returned,
        otherwise, the same document is returned.
        """
        if tool_document.uses_macros:
            try:
                document = tool_document.document
                expanded_tool_tree, _ = xml_macros.load_with_references(document.path)
                expanded_tool_tree = cast(etree._ElementTree, expanded_tool_tree)
                expanded_source = etree.tostring(expanded_tool_tree, encoding=str)
                expanded_document = Document(uri=document.uri, source=expanded_source, version=document.version)
                return GalaxyToolXmlDocument(expanded_document)
            except BaseException:
                return tool_document
        return tool_document

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
