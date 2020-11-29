from .xml.parser import XmlDocumentParser
from typing import Optional, cast

from anytree import find
from pygls.types import Range
from pygls.workspace import Document

from .xml.document import XmlDocument
from .xml.nodes import XmlElement
from .xml.types import DocumentType


class GalaxyToolXmlDocument:
    def __init__(self, document: Document) -> None:
        self.document: Document = document
        self.xml_document: XmlDocument = XmlDocumentParser().parse(document)

    @property
    def is_valid(self) -> bool:
        """Indicates if this document is a valid Galaxy Tool Wrapper
        XML document."""
        return self.xml_document.document_type == DocumentType.TOOL

    def find_element(self, name: str, maxlevel: int = 3) -> Optional[XmlElement]:
        node = find(self.xml_document, filter_=lambda node: node.name == name, maxlevel=maxlevel)
        return cast(XmlElement, node)

    def get_element_content_range(self, element: Optional[XmlElement]) -> Optional[Range]:
        if not element:
            return None
        return self.xml_document.get_element_content_range(element)


class GalaxyToolTestSnippetGenerator:
    """This class tries to generate the XML code for a test case using the information
    already defined in the inputs and outputs of the tool XML wrapper.
    """

    def __init__(self, tool_document: GalaxyToolXmlDocument) -> None:
        self.tool_document: GalaxyToolXmlDocument = tool_document

    def generate_snippet(self) -> Optional[str]:
        # TODO implement based on current tool definitions
        return "    <test>$0</test>\n"
