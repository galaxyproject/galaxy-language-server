from typing import Optional, cast
from abc import ABC, abstractmethod

from galaxy.util import xml_macros
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from lxml import etree
from pygls.types import Position
from pygls.workspace import Document

from galaxyls.types import GeneratedSnippetResult


class SnippetGenerator(ABC):
    """This abstract class defines an XML code snippet generator that can create TextMate
    snippets using the information of the tool document."""

    def __init__(self, tool_document: GalaxyToolXmlDocument) -> None:
        self.tool_document: GalaxyToolXmlDocument = self._get_expanded_tool_document(tool_document)
        self.tabstop_count: int = 0
        super().__init__()

    def generate_snippet(self) -> Optional[GeneratedSnippetResult]:
        """Generates a code snippet using this generator."""
        snippet = self._build_snippet()
        if snippet:
            insert_position = self._find_snippet_insert_position()
            return GeneratedSnippetResult(snippet, insert_position)
        return None

    @abstractmethod
    def _build_snippet(self, tabSize: int = 4) -> Optional[str]:
        """This abstract function should return the generated snippet in TextMate format or None
        if the snippet can't be generated."""
        pass

    @abstractmethod
    def _find_snippet_insert_position(self) -> Position:
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
