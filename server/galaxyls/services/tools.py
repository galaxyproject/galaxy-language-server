from typing import List, Optional, cast

from anytree import find
from galaxy.util import xml_macros
from lxml import etree
from pygls.types import Range
from pygls.workspace import Document

from .xml.document import XmlDocument
from .xml.nodes import XmlElement
from .xml.parser import XmlDocumentParser
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

    @property
    def uses_macros(self) -> bool:
        """Indicates if this tool document *uses* macro definitions.

        Returns:
            bool: True if the tool contains <expand> elements.
        """
        return self.xml_document.uses_macros

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
        self.tool_document: GalaxyToolXmlDocument = self._get_expanded_tool_document(tool_document)
        self.tabstop_count: int = 0

    def generate_snippet(self) -> Optional[str]:
        try:
            test_node = etree.Element("test")
            test_node.append(etree.Comment("Auto-generated test case, please fill in the required values"))

            inputs_node = self.tool_document.find_element("inputs")
            for input_node in inputs_node.elements:
                self._add_input_to_test(input_node, test_node)

            snippet = etree.tostring(test_node, pretty_print=True, encoding=str)
            return cast(str, snippet)
        except BaseException as e:
            print(e)
            return None

    def _add_input_to_test(self, input_node: XmlElement, test_node: etree._Element):
        switcher = {
            "param": lambda: self._add_param_to_test(input_node, test_node),
            "repeat": lambda: self._add_repeat_to_test(input_node, test_node),
            "conditional": lambda: self._add_conditional_to_test(input_node, test_node),
            "section": lambda: self._add_section_to_test(input_node, test_node),
        }
        if input_node.name:
            add_input = switcher.get(input_node.name, lambda: None)
            return add_input()

    def _add_param_to_test(self, input_node: XmlElement, test_node: etree._Element) -> None:
        param_node = etree.Element("param")
        name_attr = input_node.attributes.get("name")
        if name_attr and name_attr.value:
            param_node.attrib["name"] = name_attr.value.unquoted
        type_attr = input_node.attributes.get("type")
        if type_attr and type_attr.value:
            if type_attr.value.unquoted == "boolean":
                param_node.attrib["truevalue"] = self._get_next_tabstop()
                param_node.attrib["falsevalue"] = self._get_next_tabstop()
            elif type_attr.value.unquoted == "select":
                option_elements = input_node.elements
                options = [o.attributes.get("value").value.unquoted for o in option_elements]
                param_node.attrib["value"] = self._get_next_tabstop_with_options(options)
            else:
                param_node.attrib["value"] = self._get_next_tabstop()
        test_node.append(param_node)

    def _add_repeat_to_test(self, input_node: XmlElement, test_node: etree._Element) -> None:
        pass

    def _add_conditional_to_test(self, input_node: XmlElement, test_node: etree._Element) -> None:
        pass

    def _add_section_to_test(self, input_node: XmlElement, test_node: etree._Element) -> None:
        pass

    def _get_next_tabstop(self) -> str:
        self.tabstop_count += 1
        return f"${self.tabstop_count}"

    def _get_next_tabstop_with_options(self, options: List[str]) -> str:
        self.tabstop_count += 1
        return f"${{{self.tabstop_count}|{','.join(options)}|}}"

    def _get_expanded_tool_document(self, tool_document: GalaxyToolXmlDocument) -> GalaxyToolXmlDocument:
        if tool_document.uses_macros:
            try:
                document = tool_document.document
                expanded_tool_tree, _ = xml_macros.load_with_references(document.path)
                expanded_source = etree.tostring(expanded_tool_tree, encoding=str)
                expanded_document = Document(uri=document.uri, source=expanded_source, version=document.version)
                return GalaxyToolXmlDocument(expanded_document)
            except BaseException:
                return tool_document
        return tool_document
