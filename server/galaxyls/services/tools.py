from typing import List, Optional, cast

from anytree import find
from anytree import NodeMixin
from galaxy.util import xml_macros
from lxml import etree
from pygls.types import Range
from pygls.workspace import Document

from .xml.document import XmlDocument
from .xml.nodes import XmlElement
from .xml.parser import XmlDocumentParser
from .xml.types import DocumentType


class InputNode(NodeMixin):
    def __init__(self, name: str, element: Optional[XmlElement] = None, parent: NodeMixin = None):
        self.name: str = name
        self.element: Optional[XmlElement] = element
        self.parent = parent
        self.params: List[XmlElement] = []

    def __repr__(self) -> str:
        return self.name


class ConditionalInputNode(InputNode):
    def __init__(self, name: str, option: str, element: Optional[XmlElement] = None, parent: NodeMixin = None):
        self.option_param: XmlElement = element.elements[0]
        self.option: str = option
        super().__init__(name, element, parent)


class GalaxyToolInputTree:
    def __init__(self, inputs: Optional[XmlElement] = None) -> None:
        self._root: InputNode = InputNode("inputs", inputs)
        if inputs:
            self._root.params = inputs.get_children_with_name("param")
            self._build_input_tree(inputs, self._root)

    @property
    def leaves(self) -> List[InputNode]:
        return list(self._root.leaves)

    def _build_input_tree(self, inputs: XmlElement, parent: InputNode) -> None:
        conditionals = inputs.get_children_with_name("conditional")
        for conditional in conditionals:
            self._build_conditional_input_tree(conditional, parent)

    def _build_conditional_input_tree(self, conditional: XmlElement, parent: InputNode) -> None:
        param = conditional.elements[0]  # first child must be select or boolean
        name = conditional.get_attribute("name")
        if name and param.get_attribute("type") == "select":
            options = param.get_children_with_name("option")
            for option in options:
                option_value = option.get_attribute("value")
                if option_value:
                    conditional_node = ConditionalInputNode(name, option_value, element=conditional, parent=parent)
                    when = find(
                        conditional, filter_=lambda el: el.name == "when" and el.get_attribute("value") == option_value
                    )
                    when = cast(XmlElement, when)
                    if when:
                        conditional_node.params = when.get_children_with_name("param")
                        self._build_input_tree(when, conditional_node)


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

    def analyze_inputs(self) -> GalaxyToolInputTree:
        inputs = self.find_element("inputs")
        return GalaxyToolInputTree(inputs)


class GalaxyToolTestSnippetGenerator:
    """This class tries to generate the XML code for a test case using the information
    already defined in the inputs and outputs of the tool XML wrapper.
    """

    def __init__(self, tool_document: GalaxyToolXmlDocument) -> None:
        self.tool_document: GalaxyToolXmlDocument = self._get_expanded_tool_document(tool_document)
        self.tabstop_count: int = 0

    def generate_test_suite_snippet(self) -> Optional[str]:
        input_tree = self.tool_document.analyze_inputs()
        result_snippet = "\n".join((self._generate_test_case_snippet(input_case) for input_case in input_tree.leaves))
        return result_snippet

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

    def _generate_test_case_snippet(self, input_node: InputNode, tabSize: int = 4) -> str:
        try:
            test_node = self._create_test_node()
            current_node = test_node
            input_path = list(input_node.path)
            for node in input_path:
                node = cast(InputNode, node)
                if type(node) is ConditionalInputNode:
                    node = cast(ConditionalInputNode, node)
                    current_node = self._add_conditional_to_test(node, current_node)
                else:
                    for param in node.params:
                        self._add_param_to_node(param, test_node)
            spaces = " " * tabSize
            etree.indent(test_node, space=spaces)
            snippet = etree.tostring(test_node, pretty_print=True, encoding=str)
            return cast(str, snippet)
        except BaseException:
            return ""

    def _create_test_node(self) -> etree._Element:
        node = etree.Element("test")
        node.append(etree.Comment("Auto-generated test case, please fill in the required values"))
        node.attrib["expect_num_outputs"] = self._get_next_tabstop()
        return node

    def _add_param_to_node(self, input_node: XmlElement, test_node: etree._Element, value: Optional[str] = None) -> None:
        param_node = etree.Element("param")
        name_attr = input_node.get_attribute("name")
        if name_attr:
            param_node.attrib["name"] = name_attr
        if value:
            param_node.attrib["value"] = value
        else:
            type_attr = input_node.get_attribute("type")
            if type_attr:
                if type_attr == "boolean":
                    param_node.attrib["value"] = self._get_next_tabstop_with_options(["true", "false"])
                elif type_attr == "select" or type_attr == "text":
                    try:
                        options = self._get_options_from_param(input_node)
                        param_node.attrib["value"] = self._get_next_tabstop_with_options(options)
                    except BaseException:
                        param_node.attrib["value"] = self._get_next_tabstop()
                else:
                    param_node.attrib["value"] = self._get_next_tabstop()
        test_node.append(param_node)

    def _add_conditional_to_test(self, node: ConditionalInputNode, test_node: etree._Element) -> etree._Element:
        conditional_node = etree.Element("conditional")
        conditional_node.attrib["name"] = node.name
        # add the option param
        self._add_param_to_node(node.option_param, conditional_node, node.option)
        # add the rest of params in the corresponding when element
        for param in node.params:
            self._add_param_to_node(param, conditional_node)
        test_node.append(conditional_node)
        return conditional_node

    def _get_options_from_param(self, param: XmlElement) -> List[str]:
        option_elements = param.get_children_with_name("option")
        options = [o.get_attribute("value") for o in option_elements]
        return list(filter(None, options))

    def _get_next_tabstop(self) -> str:
        self.tabstop_count += 1
        return f"${self.tabstop_count}"

    def _get_next_tabstop_with_options(self, options: List[str]) -> str:
        if options:
            self.tabstop_count += 1
            return f"${{{self.tabstop_count}|{','.join(options)}|}}"
        return self._get_next_tabstop()
