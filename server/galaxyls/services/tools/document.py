from typing import List, Optional, cast

from anytree import find
from pygls.types import Position, Range
from pygls.workspace import Document
from galaxyls.services.tools.constants import INPUTS, OUTPUTS
from galaxyls.services.tools.inputs import GalaxyToolInputTree
from galaxyls.services.xml.nodes import XmlContainerNode, XmlElement

from galaxyls.services.xml.types import DocumentType
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.parser import XmlDocumentParser


class GalaxyToolXmlDocument:
    """Represents a Galaxy tool XML wrapper.

    This class provides access to the tool definitions and some utilities to extract
    information from the document.
    """

    def __init__(self, document: Document) -> None:
        self.document: Document = document
        self.xml_document: XmlDocument = XmlDocumentParser().parse(document)

    @property
    def is_valid(self) -> bool:
        """Indicates if this document is a valid Galaxy Tool Wrapper
        XML document."""
        return self.xml_document.document_type == DocumentType.TOOL

    @property
    def uses_macros(self) -> bool:
        """Indicates if this tool document *uses* macro definitions.

        Returns:
            bool: True if the tool contains <expand> elements.
        """
        return self.xml_document.uses_macros

    def has_section_content(self, section_name: str) -> bool:
        """Returns True if the given 'section_name' tag exists and
        can hold content, i.e. is not self closed.

        Args:
            section_name (str): The name of the tag or element.

        Returns:
            bool: True if can hold content, otherwise Fase.
        """
        section = self.find_element(section_name)
        return section is not None and not section.is_self_closed

    def find_element(self, name: str, maxlevel: int = 3) -> Optional[XmlElement]:
        """Finds the element with the given name in the document.

        Args:
            name (str): The name of the element to find.
            maxlevel (int, optional): The level at which the search will
            stop if not found. Defaults to 3.

        Returns:
            Optional[XmlElement]: The first element matching the name.
        """
        node = find(self.xml_document, filter_=lambda node: node.name == name, maxlevel=maxlevel)
        return cast(XmlElement, node)

    def get_content_range(self, element: Optional[XmlContainerNode]) -> Optional[Range]:
        """Returns the Range of the content block of the given element.

        Args:
            element (Optional[XmlElement]): The element.

        Returns:
            Optional[Range]: The Range of the content block.
        """
        if not element:
            return None
        return self.xml_document.get_content_range(element)

    def get_position_before(self, element: XmlElement) -> Position:
        """Returns the document position right before the given element opening tag.

        Args:
            element (XmlElement): The element.

        Returns:
            Position: The position right before the element opening tag.
        """
        return self.xml_document.get_position_before(element)

    def get_position_after(self, element: XmlElement) -> Position:
        """Returns the document position right after the given element closing tag.

        Args:
            element (XmlElement): The element.

        Returns:
            Position: The position right after the element closing tag.
        """
        return self.xml_document.get_position_after(element)

    def analyze_inputs(self) -> GalaxyToolInputTree:
        """Gets the inputs in the document and builds the input tree.

        Returns:
            GalaxyToolInputTree: The resulting input tree for this document.
        """
        inputs = self.find_element(INPUTS)
        return GalaxyToolInputTree(inputs)

    def get_outputs(self) -> List[XmlElement]:
        """Gets the outputs of this document as a list of elements.

        Returns:
            List[XmlElement]: The outputs defined in the document.
        """
        outputs = self.find_element(OUTPUTS)
        if outputs:
            return outputs.elements
        return []
