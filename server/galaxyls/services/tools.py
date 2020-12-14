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
DASH = "-"
UNDERSCORE = "_"


class InputNode(NodeMixin):
    """Represents a logical input node in the tool wrapper file.
    
    Each node contains references to direct children classified by their type."""
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
    """Represents a conditional input branch node in the tool wrapper file.
    
    The 'option_param' field contains the first select or boolean param and it's
    value is set to the 'option' field of one of the possible 'when' definitions.
    """
    def __init__(self, name: str, option: str, element: Optional[XmlElement] = None, parent: InputNode = None):
        super().__init__(name, element, parent)
        self.option_param: XmlElement = element.elements[0]
        self.option: str = option


class RepeatInputNode(InputNode):
    """Represents an input node that will be repeated 'min' times."""
    def __init__(self, name: str, min: int, element: Optional[XmlElement] = None):
        super().__init__(name, element, parent=None)
        self.min: int = min


class SectionInputNode(InputNode):
    """Represents a section input node which is used to group other nodes."""
    def __init__(self, name: str, element: Optional[XmlElement] = None):
        super().__init__(name, element, parent=None)


class GalaxyToolInputTree:
    """The branches of this tree contains all the inputs within a conditional path for a specific option."""
    def __init__(self, inputs: Optional[XmlElement] = None) -> None:
        self._root: InputNode = InputNode(INPUTS, inputs)
        if inputs:
            self._build_input_tree(inputs, self._root)

    @property
    def leaves(self) -> List[InputNode]:
        """The leaves of the tree contain all the final elements of the conditional branches."""
        return list(self._root.leaves)

    def _build_input_tree(self, inputs: XmlElement, parent: InputNode) -> None:
        """Given the XML element containing the inputs of the tool, this method recursively builds
        an expanded input tree.

        Args:
            inputs (XmlElement): The XML element corresponding to the inputs.
            parent (InputNode): The node that will hold all the inputs.
        """
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
        """Populates the 'parent' node with a ConditionalInputNode for each of the declared options
        in the given 'conditional' XmlElement.

        Args:
            conditional (XmlElement): The XML element (conditional tag).
            parent (InputNode): The InputNode that will hold the conditional branches and it's elements.
        """
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
        """Builds and returns a RepeatInputNode from a 'repeat' XML tag with the minimum number
        of repetitions defined.

        Args:
            repeat (XmlElement): The XML repeat tag.

        Returns:
            Optional[RepeatInputNode]: The resulting RepeatInputNode with it's own input children.
        """
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
        """Builds and returns a SectionInputNode from a 'section' XML tag.

        Args:
            section (XmlElement): The XML section tag.

        Returns:
            Optional[SectionInputNode]: The resulting SectionInputNode with it's own input children.
        """
        name = section.get_attribute(NAME)
        if name:
            section_node = SectionInputNode(name, section)
            self._build_input_tree(section, section_node)
            return section_node
        return None


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

    def find_tests_insert_position(self) -> Position:
        """Returns the position inside the document where new test cases
        can be inserted.

        If the <tests> section does not exists in the file, the best aproximate
        position where the tests should be inserted is returned (acording to the IUC
        best practices tag order).

        Returns:
            Position: The position where the test cases can be inserted in the document.
        """
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

    def get_element_content_range(self, element: Optional[XmlElement]) -> Optional[Range]:
        """Returns the Range of the content block of the given element.

        Args:
            element (Optional[XmlElement]): The element.

        Returns:
            Optional[Range]: The Range of the content block.
        """
        if not element:
            return None
        return self.xml_document.get_element_content_range(element)

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


class GalaxyToolTestSnippetGenerator:
    """This class tries to generate the XML code for a test case using the information
    already defined in the inputs and outputs of the tool XML wrapper.
    """

    def __init__(self, tool_document: GalaxyToolXmlDocument) -> None:
        self.tool_document: GalaxyToolXmlDocument = self._get_expanded_tool_document(tool_document)
        self.tabstop_count: int = 0

    def generate_test_suite_snippet(self, create_tests_section: bool = False, tabSize: int = 4) -> Optional[str]:
        """This function tries to generate a code snippet in TextMate format with all the tests cases extracted
        from the inputs and outputs of the tool.

        Args:
            create_tests_section (bool, optional): Indicates if the code snippet should
            be wrapped inside a <tests> element. Defaults to False.
            tabSize (int, optional): The number of spaces per tab. Defaults to 4.

        Returns:
            Optional[str]: The code snippet in TextMate format or None if the generation failed.
        """
        spaces = " " * tabSize
        input_tree = self.tool_document.analyze_inputs()
        outputs = self.tool_document.get_outputs()
        result_snippet = "\n".join(
            (self._generate_test_case_snippet(input_node, outputs, spaces) for input_node in input_tree.leaves)
        )
        create_tests_section = not self.tool_document.has_section_content(TESTS)
        if create_tests_section:
            return f"\n<{TESTS}>\n{result_snippet}\n</{TESTS}>"
        return result_snippet

    def _generate_test_case_snippet(self, input_node: InputNode, outputs: List[XmlElement], spaces: str = "  ") -> str:
        """Generates the code snippet for a single <test> element given an InputNode and the list of outputs
        from the tool document.

        Args:
            input_node (InputNode): The InputNode that is one of the leaves of the input tree.
            outputs (List[XmlElement]): The list of XML elements representings the outputs of the tool.
            spaces (str, optional): The str with the number of spaces for an indent level. Defaults to "  ".

        Returns:
            str: The resulting code snippet in TextMate format.
        """
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
        """Returns a XML element representing a <test> tag with the basic information.

        Returns:
            etree._Element: The <test> XML element.
        """
        node = etree.Element(TEST)
        node.append(etree.Comment(AUTO_GEN_TEST_COMMENT))
        node.attrib[EXPECT_NUM_OUTPUTS] = self._get_next_tabstop()
        return node

    def _add_inputs_to_test_element(self, input_node: InputNode, parent: etree._Element) -> None:
        """Populates the given 'parent' XML element with the tests inputs of one of the input branches.

        Given an InputNode (usually a leaf node from the input tree) the path of nodes to this InputNode
        is used to create all the input XML elements that form this conditional branch of inputs.

        Args:
            input_node (InputNode): A leaf node of the input tree.
            parent (etree._Element): The parent XML element that will hold the input XML elements of this
            input branch. This is usually a <test> element.
        """
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
        """Converts the list of XML outputs to output test elements and appends them to the 'parent' element.

        Args:
            outputs (List[XmlElement]): The lists of XML outputs definitions of the tool.
            parent (etree._Element): The XML element that will hold the resulting test outputs. Usually the <test> tag.
        """
        for output in outputs:
            if output.name == DATA:
                self._add_output_to_test(output, parent)
            elif output.name == COLLECTION:
                self._add_output_collection_to_test(output, parent)

    def _build_param_test_element(self, input_param: XmlElement, value: Optional[str] = None) -> etree._Element:
        """Builds a <param> XML element to be used in a <test> code snippet from a given input <param> XML element.

        Args:
            input_param (XmlElement): The XML element of a <param> in the tool <inputs> section.
            value (Optional[str], optional): The optional value that will be assigned to the <param>. Defaults to None.

        Returns:
            etree._Element: The XML element representing a <param> in the <test> code snippet.
        """
        param = etree.Element(PARAM)
        argument_attr = input_param.get_attribute(ARGUMENT)
        name_attr = input_param.get_attribute(NAME)
        if not name_attr and argument_attr:
            name_attr = argument_attr.lstrip(DASH).replace(DASH, UNDERSCORE)
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
        """Builds a <conditional> XML element to be used in a <test> code snippet from a given input <conditional> XML element."""
        conditional = etree.Element(CONDITIONAL)
        conditional.attrib[NAME] = input_conditional.name
        # add the option param
        param_element = self._build_param_test_element(input_conditional.option_param, input_conditional.option)
        conditional.append(param_element)
        # add the rest of params in the corresponding when element
        self._build_test_tree(input_conditional, conditional)
        return conditional

    def _build_min_repeat_test_elements(self, input_repeat: RepeatInputNode) -> List[etree._Element]:
        """Builds a <repeat> XML element to be used in a <test> code snippet from a given input <repeat> XML element."""
        repeats: List[etree._Element] = []
        for _ in range(input_repeat.min):
            repeat_node = etree.Element(REPEAT)
            repeat_node.attrib[NAME] = input_repeat.name
            self._build_test_tree(input_repeat, repeat_node)
            repeats.append(repeat_node)
        return repeats

    def _build_section_test_element(self, input_section: SectionInputNode) -> etree._Element:
        """Builds a <section> XML element to be used in a <test> code snippet from a given input <section> XML element."""
        section_node = etree.Element(SECTION)
        section_node.attrib[NAME] = input_section.name
        self._build_test_tree(input_section, section_node)
        return section_node

    def _build_test_tree(self, input: InputNode, parent: etree._Element):
        """Recursevely adds to the 'parent' XML element all the input nodes from the given 'input'.

        Args:
            input (InputNode): The InputNode to extract the node information.
            parent (etree._Element): The XML element that will contain the elements of the generated tree.
        """
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

    def _add_output_to_test(self, data: XmlElement, test_element: etree._Element) -> None:
        """Converts the given 'data' (<data>) XML element in an output XML element and adds it
        to the given <test> element.

        Args:
            output (XmlElement): The 
            test_element (etree._Element): [description]
        """
        name = data.get_attribute(NAME)
        if name:
            output_element = etree.Element(OUTPUT)
            output_element.attrib[NAME] = name
            self._add_default_asserts_to_output(output_element)
            test_element.append(output_element)

    def _add_output_collection_to_test(self, output_collection: XmlElement, test_element: etree._Element) -> None:
        """Adds the 'output_collection' XML element to the 'test_element' with a default <element>.

        Args:
            output_collection (XmlElement): The <collection> XML element.
            test_element (etree._Element): The <test> XML element.
        """
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
        """Given a XML element (usually an output), this method adds the <assert_contents> tag
        with some examples of asserts.

        Args:
            output (etree._Element): The output XML element of the <test> that will contain
            the <assert_contents>.
        """
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
        """Gets the list of children elements of type <option> from the given 'param' XML element.

        Args:
            param (XmlElement): The <param> XML element.

        Returns:
            List[str]: The list of <option> in this 'param' or an empty list.
        """
        option_elements = param.get_children_with_name(OPTION)
        options = [o.get_attribute(VALUE) for o in option_elements]
        return list(filter(None, options))

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

    def _get_next_tabstop_with_options(self, options: List[str]) -> str:
        """Gets the current tabstop with a list of possible options.

        If the list is empty, a normal tabstop is returned.

        Args:
            options (List[str]): The list of options that can be selected in this tabstop.

        Returns:
            str: The current tabstop with all the available options.
        """
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
