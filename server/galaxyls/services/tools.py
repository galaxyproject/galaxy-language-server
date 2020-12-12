from typing import List, Optional, cast

from anytree import NodeMixin, RenderTree, find
from galaxy.util import xml_macros
from lxml import etree
from pygls.types import Position, Range
from pygls.workspace import Document

from .xml.document import XmlDocument
from .xml.nodes import XmlElement
from .xml.parser import XmlDocumentParser
from .xml.types import DocumentType

INPUTS = "inputs"
PARAM = "param"
CONDITIONAL = "conditional"
REPEAT = "repeat"
SECTION = "section"
NAME = "name"
TYPE = "type"
SELECT = "select"
OPTION = "option"
VALUE = "value"
WHEN = "when"
TEST = "test"
TESTS = "tests"
TEXT = "text"
MIN = "min"
BOOLEAN = "boolean"
ARGUMENT = "argument"
BOOLEAN_OPTIONS = ["true", "false"]
EXPECT_NUM_OUTPUTS = "expect_num_outputs"
OUTPUTS = "outputs"
DATA = "data"
COLLECTION = "collection"
OUTPUT = "output"
OUTPUT_COLLECTION = "output_collection"
ASSERT_CONTENTS = "assert_contents"
HAS_TEXT = "has_text"
HAS_LINE = "has_line"
HAS_LINE_MATCHING = "has_line_matching"
HAS_N_COLUMNS = "has_n_columns"
HAS_SIZE = "has_size"
LINE = "line"
EXPRESSION = "expression"
N = "n"
DELTA = "delta"
ELEMENT = "element"
AUTO_GEN_TEST_COMMENT = "TODO: auto-generated test case. Please fill in the required values"


class InputNode(NodeMixin):
    def __init__(self, name: str, element: Optional[XmlElement] = None, parent: NodeMixin = None):
        self.name: str = name
        self.element: Optional[XmlElement] = element
        self.parent = parent
        self.params: List[XmlElement] = []
        self.repeats: List[RepeatInputNode] = []
        self.sections: List[SectionInputNode] = []

    def __repr__(self) -> str:
        return self.name


class ConditionalInputNode(InputNode):
    def __init__(self, name: str, option: str, element: Optional[XmlElement] = None, parent: InputNode = None):
        super().__init__(name, element, parent)
        self.option_param: XmlElement = element.elements[0]
        self.option: str = option


class RepeatInputNode(InputNode):
    def __init__(self, name: str, min: int, element: Optional[XmlElement] = None):
        super().__init__(name, element, parent=None)
        self.min: int = min


class SectionInputNode(InputNode):
    def __init__(self, name: str, element: Optional[XmlElement] = None):
        super().__init__(name, element, parent=None)


class GalaxyToolInputTree:
    def __init__(self, inputs: Optional[XmlElement] = None) -> None:
        self._root: InputNode = InputNode(INPUTS, inputs)
        if inputs:
            self._build_input_tree(inputs, self._root)

    @property
    def leaves(self) -> List[InputNode]:
        return list(self._root.leaves)

    def _build_input_tree(self, inputs: XmlElement, parent: InputNode) -> None:
        parent.params = inputs.get_children_with_name(PARAM)

        conditionals = inputs.get_children_with_name(CONDITIONAL)
        for conditional in conditionals:
            self._build_conditional_input_tree(conditional, parent)

        repeats = inputs.get_children_with_name(REPEAT)
        for repeat in repeats:
            repeat_node = self._build_repeat_input_tree(repeat)
            if repeat_node:
                parent.repeats.append(repeat_node)

        sections = inputs.get_children_with_name(SECTION)
        for section in sections:
            section_node = self._build_section_input_tree(section)
            if section_node:
                parent.sections.append(section_node)

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
                        self._build_input_tree(when, conditional_node)
        # TODO: support boolean

    def _build_repeat_input_tree(self, repeat: XmlElement) -> Optional[RepeatInputNode]:
        name = repeat.get_attribute(NAME)
        if name:
            min = 1
            min_attr = repeat.get_attribute(MIN)
            if min_attr and min_attr.isdigit:
                min = int(min_attr)
            repeat_node = RepeatInputNode(name, min, repeat)
            self._build_input_tree(repeat, repeat_node)
            return repeat_node
        return None

    def _build_section_input_tree(self, section: XmlElement) -> Optional[SectionInputNode]:
        name = section.get_attribute(NAME)
        if name:
            section_node = SectionInputNode(name, section)
            self._build_input_tree(section, section_node)
            return section_node
        return None


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

    def find_tests_insert_position(self) -> Position:
        section = self.find_element(TESTS)
        if section:
            content_range = self.get_element_content_range(section)
            if content_range:
                return content_range.end
            else:  # is self closed <tests/>
                return self.get_position_before(section)
        else:
            section = self.find_element(OUTPUTS)
            if section:
                return self.get_position_after(section)
            section = self.find_element(INPUTS)
            if section:
                return self.get_position_after(section)
            return Position()

    def has_section_content(self, section_name: str) -> bool:
        section = self.find_element(section_name)
        return section is not None and not section.is_self_closed

    def find_element(self, name: str, maxlevel: int = 3) -> Optional[XmlElement]:
        node = find(self.xml_document, filter_=lambda node: node.name == name, maxlevel=maxlevel)
        return cast(XmlElement, node)

    def get_element_content_range(self, element: Optional[XmlElement]) -> Optional[Range]:
        if not element:
            return None
        return self.xml_document.get_element_content_range(element)

    def get_position_before(self, element: XmlElement) -> Position:
        return self.xml_document.get_position_before(element)

    def get_position_after(self, element: XmlElement) -> Position:
        return self.xml_document.get_position_after(element)

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

    def generate_test_suite_snippet(self, create_tests_section: bool = False, tabSize: int = 4) -> Optional[str]:
        spaces = " " * tabSize
        input_tree = self.tool_document.analyze_inputs()
        print(RenderTree(input_tree._root))
        outputs = self.tool_document.get_outputs()
        result_snippet = "\n".join(
            (self._generate_test_case_snippet(input_node, outputs, spaces) for input_node in input_tree.leaves)
        )
        create_tests_section = not self.tool_document.has_section_content(TESTS)
        if create_tests_section:
            return f"\n<{TESTS}>\n{result_snippet}\n</{TESTS}>"
        return result_snippet

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

    def _create_test_element(self) -> etree._Element:
        node = etree.Element(TEST)
        node.append(etree.Comment(AUTO_GEN_TEST_COMMENT))
        node.attrib[EXPECT_NUM_OUTPUTS] = self._get_next_tabstop()
        return node

    def _add_inputs_to_test_element(self, input_node: InputNode, parent: etree._Element) -> None:
        current_parent = parent
        input_path = list(input_node.path)
        # 'input_path' contains the input nodes composing this conditional branch of inputs
        for node in input_path:
            node = cast(InputNode, node)
            if type(node) is ConditionalInputNode:
                conditional_element = self._build_conditional_test_element(node)
                current_parent.append(conditional_element)
                current_parent = conditional_element
            else:
                self._build_test_tree(node, current_parent)

    def _add_outputs_to_test_element(self, outputs: List[XmlElement], parent: etree._Element) -> None:
        for output in outputs:
            if output.name == DATA:
                self._add_output_to_test(output, parent)
            elif output.name == COLLECTION:
                self._add_output_collection_to_test(output, parent)

    def _build_param_test_element(self, input_param: XmlElement, value: Optional[str] = None) -> etree._Element:
        param = etree.Element(PARAM)
        argument_attr = input_param.get_attribute(ARGUMENT)
        name_attr = input_param.get_attribute(NAME)
        if not name_attr and argument_attr:
            name_attr = argument_attr.lstrip("-")
        if name_attr:
            param.attrib[NAME] = name_attr
        default_value = input_param.get_attribute(VALUE)
        if value:
            param.attrib[VALUE] = value
        elif default_value:
            param.attrib[VALUE] = self._get_next_tabstop_with_placeholder(default_value)
        else:
            type_attr = input_param.get_attribute(TYPE)
            if type_attr:
                if type_attr == BOOLEAN:
                    param.attrib[VALUE] = self._get_next_tabstop_with_options(BOOLEAN_OPTIONS)
                elif type_attr == SELECT or type_attr == TEXT:
                    try:
                        options = self._get_options_from_param(input_param)
                        param.attrib[VALUE] = self._get_next_tabstop_with_options(options)
                    except BaseException:
                        param.attrib[VALUE] = self._get_next_tabstop()
                else:
                    param.attrib[VALUE] = self._get_next_tabstop()
        return param

    def _build_conditional_test_element(self, input_conditional: ConditionalInputNode) -> etree._Element:
        conditional = etree.Element(CONDITIONAL)
        conditional.attrib[NAME] = input_conditional.name
        # add the option param
        param_element = self._build_param_test_element(input_conditional.option_param, input_conditional.option)
        conditional.append(param_element)
        # add the rest of params in the corresponding when element
        self._build_test_tree(input_conditional, conditional)
        return conditional

    def _build_min_repeat_test_elements(self, input_repeat: RepeatInputNode) -> List[etree._Element]:
        repeats: List[etree._Element] = []
        for _ in range(input_repeat.min):
            repeat_node = etree.Element(REPEAT)
            repeat_node.attrib[NAME] = input_repeat.name
            self._build_test_tree(input_repeat, repeat_node)
            repeats.append(repeat_node)
        return repeats

    def _build_section_test_element(self, input_section: SectionInputNode) -> etree._Element:
        section_node = etree.Element(SECTION)
        section_node.attrib[NAME] = input_section.name
        self._build_test_tree(input_section, section_node)
        return section_node

    def _build_test_tree(self, input: InputNode, parent: etree._Element):
        for param in input.params:
            param_element = self._build_param_test_element(param)
            parent.append(param_element)
        for repeat in input.repeats:
            repeat_elements = self._build_min_repeat_test_elements(repeat)
            for rep in repeat_elements:
                parent.append(rep)
        for section in input.sections:
            section_element = self._build_section_test_element(section)
            parent.append(section_element)

    def _add_output_to_test(self, output: XmlElement, test_element: etree._Element) -> None:
        name = output.get_attribute(NAME)
        if name:
            output_element = etree.Element(OUTPUT)
            output_element.attrib[NAME] = name
            self._add_default_asserts_to_output(output_element)
            test_element.append(output_element)

    def _add_output_collection_to_test(self, output_collection: XmlElement, test_element: etree._Element) -> None:
        name = output_collection.get_attribute(NAME)
        if name:
            output_element = etree.Element(OUTPUT_COLLECTION)
            output_element.attrib[NAME] = name
            type_attr = output_collection.get_attribute(TYPE)
            if type_attr:
                output_element.attrib[TYPE] = type_attr
            element = etree.Element(ELEMENT)
            element.attrib[NAME] = self._get_next_tabstop()
            self._add_default_asserts_to_output(element)
            output_element.append(element)
            test_element.append(output_element)

    def _add_default_asserts_to_output(self, output: etree._Element) -> None:
        assert_contents = etree.Element(ASSERT_CONTENTS)

        has_text = etree.Element(HAS_TEXT)
        has_text.attrib[TEXT] = self._get_next_tabstop()
        assert_contents.append(has_text)

        has_line = etree.Element(HAS_LINE)
        has_line.attrib[LINE] = self._get_next_tabstop()
        assert_contents.append(has_line)

        has_line_matching = etree.Element(HAS_LINE_MATCHING)
        has_line_matching.attrib[EXPRESSION] = self._get_next_tabstop()
        assert_contents.append(has_line_matching)

        has_n_columns = etree.Element(HAS_N_COLUMNS)
        has_n_columns.attrib[N] = self._get_next_tabstop()
        assert_contents.append(has_n_columns)

        has_size = etree.Element(HAS_SIZE)
        has_size.attrib[VALUE] = self._get_next_tabstop()
        has_size.attrib[DELTA] = self._get_next_tabstop()
        assert_contents.append(has_size)

        output.append(assert_contents)

    def _get_options_from_param(self, param: XmlElement) -> List[str]:
        option_elements = param.get_children_with_name(OPTION)
        options = [o.get_attribute(VALUE) for o in option_elements]
        return list(filter(None, options))

    def _get_next_tabstop(self) -> str:
        self.tabstop_count += 1
        return f"${self.tabstop_count}"

    def _get_next_tabstop_with_placeholder(self, placeholder: str) -> str:
        self.tabstop_count += 1
        return f"${{{self.tabstop_count}:{placeholder}}}"

    def _get_next_tabstop_with_options(self, options: List[str]) -> str:
        if options:
            self.tabstop_count += 1
            return f"${{{self.tabstop_count}|{','.join(options)}|}}"
        return self._get_next_tabstop()

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
