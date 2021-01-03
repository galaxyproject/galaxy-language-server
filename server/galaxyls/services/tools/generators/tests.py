from typing import List, Optional, Union, cast

from galaxyls.services.tools.constants import (
    ARGUMENT,
    ASSERT_CONTENTS,
    BOOLEAN,
    BOOLEAN_OPTIONS,
    CHECKED,
    COLLECTION,
    CONDITIONAL,
    DATA,
    DELTA,
    ELEMENT,
    EXPECT_NUM_OUTPUTS,
    EXPRESSION,
    HAS_LINE,
    HAS_LINE_MATCHING,
    HAS_N_COLUMNS,
    HAS_SIZE,
    HAS_TEXT,
    INPUTS,
    LINE,
    NAME,
    OPTION,
    OUTPUT,
    OUTPUT_COLLECTION,
    OUTPUTS,
    PARAM,
    REPEAT,
    SECTION,
    SELECT,
    TEST,
    TESTS,
    TEXT,
    TOOL,
    TYPE,
    VALUE,
    N,
)
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.tools.generators.snippets import SnippetGenerator
from galaxyls.services.tools.inputs import ConditionalInputNode, InputNode, RepeatInputNode, SectionInputNode
from galaxyls.services.xml.nodes import XmlElement
from lxml import etree
from pygls.types import Position, Range

AUTO_GEN_TEST_COMMENT = "TODO: auto-generated test case. Please fill in the required values"
BOOLEAN_CONDITIONAL_NOT_RECOMMENDED_COMMENT = (
    "Warning: the use of boolean as a conditional parameter is not recommended. Please consider using a select instead."
)


class GalaxyToolTestSnippetGenerator(SnippetGenerator):
    """This class tries to generate the XML code for a test case using the information
    already defined in the inputs and outputs of the tool XML wrapper.
    """

    def __init__(self, tool_document: GalaxyToolXmlDocument, tabSize: int = 4) -> None:
        super().__init__(tool_document, tabSize)

    def _build_snippet(self) -> Optional[str]:
        """This function tries to generate a code snippet in TextMate format with all the tests cases extracted
        from the inputs and outputs of the tool.

        Returns:
            Optional[str]: The code snippet in TextMate format or None if the generation failed.
        """
        input_tree = self.expanded_document.analyze_inputs()
        outputs = self.expanded_document.get_outputs()
        result_snippet = "\n".join((self._generate_test_case_snippet(input_node, outputs) for input_node in input_tree.leaves))
        tests_section = self.tool_document.find_element(TESTS)
        if tests_section and not tests_section.is_self_closed:
            return result_snippet
        return f"\n<{TESTS}>\n{result_snippet}\n</{TESTS}>"

    def _find_snippet_insert_position(self) -> Union[Position, Range]:
        """Returns the position inside the document where new test cases
        can be inserted.

        If the <tests> section does not exists in the file, the best aproximate
        position where the tests should be inserted is returned (acording to the IUC
        best practices tag order).

        Returns:
            Position: The position where the test cases can be inserted in the document.
        """
        tool = self.tool_document
        section = tool.find_element(TESTS)
        if section:
            content_range = tool.get_content_range(section)
            if content_range:
                return content_range.end
            else:  # is self closed <tests/>
                start = tool.get_position_before(section)
                end = tool.get_position_after(section)
                return Range(start, end)
        else:
            section = tool.find_element(OUTPUTS)
            if section:
                return tool.get_position_after(section)
            section = tool.find_element(INPUTS)
            if section:
                return tool.get_position_after(section)
            section = tool.find_element(TOOL)
            if section:
                return tool.get_content_range(section).end
            return Position()

    def _generate_test_case_snippet(self, input_node: InputNode, outputs: List[XmlElement]) -> str:
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
            etree.indent(test_element, space=self.indent_spaces)
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
            name_attr = self._extract_name_from_argument(argument_attr)
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
                    default_value = input_param.get_attribute(CHECKED)
                    param.attrib[VALUE] = self._get_next_tabstop_with_options(BOOLEAN_OPTIONS, default_value)
                elif type_attr == SELECT or type_attr == TEXT:
                    try:
                        options = self._get_options_from_param(input_param)
                        param.attrib[VALUE] = self._get_next_tabstop_with_options(options, default_value)
                    except BaseException:
                        param.attrib[VALUE] = self._get_next_tabstop()
                else:
                    param.attrib[VALUE] = self._get_next_tabstop()
        return param

    def _build_conditional_test_element(self, input_conditional: ConditionalInputNode) -> etree._Element:
        """Builds a <conditional> XML element to be used in a <test> code snippet from a
        given input <conditional> XML element."""
        conditional = etree.Element(CONDITIONAL)
        conditional.attrib[NAME] = input_conditional.name
        # add the option param
        param_element = self._build_param_test_element(input_conditional.option_param, input_conditional.option)
        if input_conditional.option_param.get_attribute(TYPE) == BOOLEAN:
            conditional.append(etree.Comment(BOOLEAN_CONDITIONAL_NOT_RECOMMENDED_COMMENT))
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
