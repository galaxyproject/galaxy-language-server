from typing import Optional, cast
from abc import ABC, abstractmethod

from galaxy.util import xml_macros
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from lxml import etree
from pygls.types import Position
from pygls.workspace import Document


class SnippetGenerator(ABC):
    """This abstract class defines an XML code snippet generator that can create TextMate
    snippets using the information of the tool document."""

    def __init__(self, tool_document: GalaxyToolXmlDocument) -> None:
        self.tool_document: GalaxyToolXmlDocument = self._get_expanded_tool_document(tool_document)
        self.tabstop_count: int = 0
        super().__init__()

    @abstractmethod
    def generate_snippet(self, tabSize: int = 4) -> Optional[str]:
        pass

    @abstractmethod
    def find_snippet_insert_position(self, tool: GalaxyToolXmlDocument) -> Position:
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
