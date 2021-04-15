from pathlib import Path
from typing import Dict, List, Optional, cast

from anytree import find
from pygls.lsp.types import Position, Range
from pygls.workspace import Document
from galaxyls.services.tools.constants import IMPORT, INPUTS, MACROS, OUTPUTS, TESTS, TOOL
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

    def __init__(self, document: Document, xml_document: Optional[XmlDocument] = None) -> None:
        if xml_document:
            self.xml_document = xml_document
            self.document: Document = xml_document.document
        else:
            self.document: Document = document
            self.xml_document = XmlDocumentParser().parse(document)

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

    @property
    def source(self) -> str:
        """The contents of the tool document."""
        return self.xml_document.document.source

    @property
    def path(self) -> str:
        """The file path of the tool."""
        return self.xml_document.document.path

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
        if element:
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

    def get_tool_element(self) -> Optional[XmlElement]:
        """Gets the root tool element"""
        return self.find_element(TOOL)

    def get_macros_element(self) -> Optional[XmlElement]:
        """Gets the macros element"""
        return self.find_element(MACROS)

    def get_macro_import_elements(self) -> Optional[List[XmlElement]]:
        """Gets the list of elements with macro file import declarations."""
        return self.xml_document.find_all_elements_with_name(IMPORT)

    def get_macro_import_uris(self) -> Dict[str, str]:
        """Returns a dictionary with the file name and corresponding file uri of each
        imported macro file."""
        result = {}
        tool_directory = self._get_tool_directory()
        import_elements = self.get_macro_import_elements()
        for imp in import_elements:
            filename = imp.get_content(self.xml_document.document.source)
            if filename:
                path = tool_directory / filename
                if path.exists():
                    file_uri = path.as_uri()
                    result[filename] = file_uri
        return result

    def get_macros_range(self) -> Optional[Range]:
        """Returns the Range position of the macros element name if it exists."""
        element = self.get_macros_element()
        if element:
            range = self.xml_document.get_element_name_range(element)
            return range

    def get_import_macro_file_range(self, file_path: Optional[str]) -> Optional[Range]:
        """Returns the Range position of the imported macro file element if it exists."""
        if file_path:
            filename = Path(file_path).name
            import_elements = self.get_macro_import_elements()
            for imp in import_elements:
                imp_filename = imp.get_content(self.xml_document.document.source)
                if imp_filename == filename:
                    return self.xml_document.get_full_range(imp)

    def get_tool_id(self) -> Optional[str]:
        """Gets the identifier of the tool"""
        tool_element = self.get_tool_element()
        return tool_element.get_attribute("id")

    def get_tests(self) -> List[XmlElement]:
        """Gets the tests of this document as a list of elements.

        Returns:
            List[XmlElement]: The tests defined in the document.
        """
        tests = self.find_element(TESTS)
        if tests:
            return tests.elements
        return []

    @classmethod
    def from_xml_document(cls, xml_document: XmlDocument) -> "GalaxyToolXmlDocument":
        return GalaxyToolXmlDocument(xml_document.document, xml_document)

    def _get_tool_directory(self):
        tool_directory = Path(self.xml_document.document.path).resolve().parent
        return tool_directory
