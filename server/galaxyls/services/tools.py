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


INPUTS = "inputs"
PARAM = "param"
CONDITIONAL = "conditional"
NAME = "name"
TYPE = "type"
SELECT = "select"
OPTION = "option"
VALUE = "value"
WHEN = "when"
TEST = "test"
TEXT = "text"
BOOLEAN = "boolean"
BOOLEAN_OPTIONS = ["true", "false"]
EXPECT_NUM_OUTPUTS = "expect_num_outputs"
OUTPUTS = "outputs"
DATA = "data"
COLLECTION = "collection"
OUTPUT = "output"
OUTPUT_COLLECTION = "output_collection"
AUTO_GEN_TEST_COMMENT = "TODO: auto-generated test case. Please fill in the required values"


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
        self._root: InputNode = InputNode(INPUTS, inputs)
        if inputs:
            self._root.params = inputs.get_children_with_name(PARAM)
            self._build_input_tree(inputs, self._root)

    @property
    def leaves(self) -> List[InputNode]:
        return list(self._root.leaves)

    def _build_input_tree(self, inputs: XmlElement, parent: InputNode) -> None:
        conditionals = inputs.get_children_with_name(CONDITIONAL)
        for conditional in conditionals:
            self._build_conditional_input_tree(conditional, parent)

    def _build_conditional_input_tree(self, conditional: XmlElement, parent: InputNode) -> None:
        param = conditional.elements[0]  # first child must be select or boolean
        name = conditional.get_attribute(NAME)
        if name and param.get_attribute(TYPE) == SELECT:
            options = param.get_children_with_name(OPTION)
            for option in options:
                option_value = option.get_attribute(VALUE)
                if option_value:
                    conditional_node = ConditionalInputNode(name, option_value, element=conditional, parent=parent)
                    when = find(conditional, filter_=lambda el: el.name == WHEN and el.get_attribute(VALUE) == option_value)
                    when = cast(XmlElement, when)
                    if when:
                        conditional_node.params = when.get_children_with_name(PARAM)
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
        inputs = self.find_element(INPUTS)
        return GalaxyToolInputTree(inputs)

    def get_outputs(self) -> List[XmlElement]:
        outputs = self.find_element(OUTPUTS)
        if outputs:
            return outputs.elements
        return []


class GalaxyToolTestSnippetGenerator:
    """This class tries to generate the XML code for a test case using the information
    already defined in the inputs and outputs of the tool XML wrapper.
    """

    def __init__(self, tool_document: GalaxyToolXmlDocument) -> None:
        self.tool_document: GalaxyToolXmlDocument = self._get_expanded_tool_document(tool_document)
        self.tabstop_count: int = 0

    def generate_test_suite_snippet(self, tabSize: int = 4) -> Optional[str]:
        spaces = " " * tabSize
        input_tree = self.tool_document.analyze_inputs()
        outputs = self.tool_document.get_outputs()
        result_snippet = "\n".join(
            (self._generate_test_case_snippet(input_node, outputs, spaces) for input_node in input_tree.leaves)
        )
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

    def _generate_test_case_snippet(self, input_node: InputNode, outputs: List[XmlElement], spaces: str = "  ") -> str:
        try:
            test_element = self._create_test_element()
            self._add_inputs_to_test_element(input_node, test_element)
            self._add_outputs_to_test_element(outputs, test_element)
            etree.indent(test_element, space=spaces)
            snippet = etree.tostring(test_element, pretty_print=True, encoding=str)
            return cast(str, snippet)
        except BaseException:
            return ""

    def _add_inputs_to_test_element(self, input_node: InputNode, test_element: etree._Element) -> None:
        current_element = test_element
        input_path = list(input_node.path)
        # 'input_path' contains the input nodes composing this conditional branch of inputs
        for node in input_path:
            node = cast(InputNode, node)
            if type(node) is ConditionalInputNode:
                node = cast(ConditionalInputNode, node)
                current_element = self._add_conditional_to_test(node, current_element)
            else:
                for param in node.params:
                    self._add_param_to_test(param, test_element)

    def _add_outputs_to_test_element(self, outputs: List[XmlElement], test_element: etree._Element) -> None:
        for output in outputs:
            if output.name == DATA:
                self._add_output_to_test(output, test_element)
            elif output.name == COLLECTION:
                self._add_output_collection_to_test(output, test_element)

    def _create_test_element(self) -> etree._Element:
        node = etree.Element(TEST)
        node.append(etree.Comment(AUTO_GEN_TEST_COMMENT))
        node.attrib[EXPECT_NUM_OUTPUTS] = self._get_next_tabstop()
        return node

    def _add_param_to_test(self, input_node: XmlElement, test_element: etree._Element, value: Optional[str] = None) -> None:
        param_node = etree.Element(PARAM)
        name_attr = input_node.get_attribute(NAME)
        if name_attr:
            param_node.attrib[NAME] = name_attr
        if value:
            param_node.attrib[VALUE] = value
        else:
            type_attr = input_node.get_attribute(TYPE)
            if type_attr:
                if type_attr == BOOLEAN:
                    param_node.attrib[VALUE] = self._get_next_tabstop_with_options(BOOLEAN_OPTIONS)
                elif type_attr == SELECT or type_attr == TEXT:
                    try:
                        options = self._get_options_from_param(input_node)
                        param_node.attrib[VALUE] = self._get_next_tabstop_with_options(options)
                    except BaseException:
                        param_node.attrib[VALUE] = self._get_next_tabstop()
                else:
                    param_node.attrib[VALUE] = self._get_next_tabstop()
        test_element.append(param_node)

    def _add_conditional_to_test(self, node: ConditionalInputNode, test_element: etree._Element) -> etree._Element:
        conditional_node = etree.Element(CONDITIONAL)
        conditional_node.attrib[NAME] = node.name
        # add the option param
        self._add_param_to_test(node.option_param, conditional_node, node.option)
        # add the rest of params in the corresponding when element
        for param in node.params:
            self._add_param_to_test(param, conditional_node)
        test_element.append(conditional_node)
        return conditional_node

    def _add_output_to_test(self, output: XmlElement, test_element: etree._Element) -> None:
        name = output.get_attribute(NAME)
        if name:
            output_element = etree.Element(OUTPUT)
            output_element.attrib[NAME] = name
            output_element.text = self._get_next_tabstop()
            test_element.append(output_element)

    def _add_output_collection_to_test(self, output_collection: XmlElement, test_element: etree._Element) -> None:
        name = output_collection.get_attribute(NAME)
        if name:
            output_element = etree.Element(OUTPUT_COLLECTION)
            output_element.attrib[NAME] = name
            type_attr = output_collection.get_attribute(TYPE)
            if type_attr:
                output_element.attrib[TYPE] = type_attr
            output_element.text = self._get_next_tabstop()
            test_element.append(output_element)

    def _get_options_from_param(self, param: XmlElement) -> List[str]:
        option_elements = param.get_children_with_name(OPTION)
        options = [o.get_attribute(VALUE) for o in option_elements]
        return list(filter(None, options))

    def _get_next_tabstop(self) -> str:
        self.tabstop_count += 1
        return f"${self.tabstop_count}"

    def _get_next_tabstop_with_options(self, options: List[str]) -> str:
        if options:
            self.tabstop_count += 1
            return f"${{{self.tabstop_count}|{','.join(options)}|}}"
        return self._get_next_tabstop()
