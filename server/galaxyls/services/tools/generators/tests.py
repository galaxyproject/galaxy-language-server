from typing import (
    List,
    Optional,
    Set,
    Tuple,
    Union,
    cast,
)

from anytree import NodeMixin, PreOrderIter
from lsprotocol.types import (
    Position,
    Range,
)
from lxml import etree

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
from galaxyls.services.tools.generators import DisplayableException
from galaxyls.services.tools.generators.snippets import SnippetGenerator, WorkspaceEditsGenerator
from galaxyls.services.tools.inputs import (
    ConditionalInputNode,
    InputNode,
    RepeatInputNode,
    SectionInputNode,
)
from galaxyls.services.xml.nodes import XmlElement
from galaxyls.types import ReplaceTextRangeResult

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

    def _build_snippet(self) -> Tuple[str, bool]:
        """This function tries to generate a code snippet in TextMate format with all the tests cases extracted
        from the inputs and outputs of the tool.

        Returns:
            Tuple[str, bool]: The code snippet in TextMate format or an error message if the generation failed.
            The second value of the tuple indicates if there was an error.
        """
        try:
            input_tree = self.expanded_document.analyze_inputs()
            outputs = self.expanded_document.get_outputs()
            result_snippet = "\n".join(
                (self._generate_test_case_snippet(input_node, outputs) for input_node in input_tree.leaves)
            )
            tests_section = self.tool_document.find_element(TESTS)
            if tests_section and not tests_section.is_self_closed:
                return (result_snippet, False)
            return (f"\n<{TESTS}>\n{result_snippet}\n</{TESTS}>", False)
        except BaseException as ex:
            return (f"Automatic Test Case generation failed with reason: {ex}", True)

    def _find_snippet_insert_position(self) -> Union[Position, Range]:
        """Returns the position inside the document where new test cases
        can be inserted.

        If the <tests> section does not exists in the file, the best approximate
        position where the tests should be inserted is returned (according to the IUC
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
                return Range(start=start, end=end)
        else:
            section = tool.find_element(OUTPUTS)
            if section:
                return tool.get_position_after(section)
            section = tool.find_element(INPUTS)
            if section:
                return tool.get_position_after(section)
            section = tool.find_element(TOOL)
            if section:
                content_range = tool.get_content_range(section)
                if content_range:
                    return content_range.end
            return Position(line=0, character=0)

    def _generate_test_case_snippet(self, input_node: InputNode, outputs: List[XmlElement]) -> str:
        """Generates the code snippet for a single <test> element given an InputNode and the list of outputs
        from the tool document.

        Args:
            input_node (InputNode): The InputNode that is one of the leaves of the input tree.
            outputs (List[XmlElement]): The list of XML elements representing the outputs of the tool.
            spaces (str, optional): The str with the number of spaces for an indent level. Defaults to "  ".

        Returns:
            str: The resulting code snippet in TextMate format.
        """
        test_element = self._create_test_element()
        self._add_inputs_to_test_element(input_node, test_element)
        self._add_outputs_to_test_element(outputs, test_element)
        etree.indent(test_element, space=self.indent_spaces)
        snippet = etree.tostring(test_element, pretty_print=True, encoding=str)
        return snippet

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
        argument_attr = input_param.get_attribute_value(ARGUMENT)
        name_attr = input_param.get_attribute_value(NAME)
        if not name_attr and argument_attr:
            name_attr = self._extract_name_from_argument(argument_attr)
        if name_attr:
            param.attrib[NAME] = name_attr
        default_value = input_param.get_attribute_value(VALUE)
        if value:
            param.attrib[VALUE] = value
        elif default_value:
            param.attrib[VALUE] = self._get_next_tabstop_with_placeholder(default_value)
        else:
            type_attr = input_param.get_attribute_value(TYPE)
            if type_attr:
                if type_attr == BOOLEAN:
                    default_value = input_param.get_attribute_value(CHECKED)
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
        if input_conditional.option_param:
            # add the option param
            param_element = self._build_param_test_element(input_conditional.option_param, input_conditional.option)
            if input_conditional.option_param.get_attribute_value(TYPE) == BOOLEAN:
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

    def _build_test_tree(self, input: InputNode, parent: etree._Element) -> None:
        """Recursively adds to the 'parent' XML element all the input nodes from the given 'input'.

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
        name = data.get_attribute_value(NAME)
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
        name = output_collection.get_attribute_value(NAME)
        if name:
            output_element = etree.Element(OUTPUT_COLLECTION)
            output_element.attrib[NAME] = name
            type_attr = output_collection.get_attribute_value(TYPE)
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
        options = [o.get_attribute_value(VALUE) for o in option_elements]
        return list(filter(None, options))


class ParameterNode(NodeMixin):
    """This class helps to build a tree structure with the hierarchy of test params based on the
    input parameters of the tool XML wrapper.

    The element attribute is used to store the XML element (conditional, repeat, section, etc.)
    that is the container of a group of test parameters.
    The test_parameters attribute is used to store the list of test parameters that are children
    of this node.
    """

    def __init__(
        self,
        name: str,
        parent=None,
        container_element: Optional[XmlElement] = None,
        test_parameters: Optional[List[XmlElement]] = None,
    ):
        super().__init__()
        self.name = name
        self.element = container_element
        self.parent = parent
        self.test_parameters = test_parameters

    def __repr__(self):
        return f"TreeNode(name={self.name}, element={self.element}, data={self.test_parameters})"


def find_node_by_key(root: ParameterNode, key: str) -> Optional[ParameterNode]:
    """Finds a node in the tree by its key."""
    for node in PreOrderIter(root):
        if node.name == key:
            return node
    return None


class GalaxyToolTestUpdater(WorkspaceEditsGenerator):
    """This class tries to update the test cases in the XML document with the information
    already defined in the inputs and outputs of the tool XML wrapper.
    """

    def __init__(self, tool_document: GalaxyToolXmlDocument, tabSize: int = 4) -> None:
        super().__init__(tool_document, tabSize)

    def _build_workspace_edits(self) -> List[ReplaceTextRangeResult]:
        """This function tries to generate a code snippet with the existing test cases but
        with the correct syntax when using conditional, sections, repeats, etc.

        For example, if the inputs are defined like this:

            <section name="sectionA">
                <param name="param1" type="text"/>
                ...
            </section>

        And the test declares a param without the section:
            <test>
                <param name="param1" value="value1"/>
                ...

        The generated XML will look like this:
            <test>
                <section name="sectionA">
                    <param name="param1" value="value1"/>
                </section>
                ...

        Returns:
            List[ReplaceTextRangeResult]: The list of workspace edits to be applied to the document.
        """
        result_edits: List[ReplaceTextRangeResult] = []
        try:
            existing_tests = self.tool_document.get_tests()
            if not existing_tests:
                raise DisplayableException("Tool does not contain any test cases")

            input_params = self.expanded_document.get_input_params()

            for test in existing_tests:
                test_edits = self._generate_edits_for_test_element(test, input_params)
                result_edits.extend(test_edits)

            return result_edits
        except BaseException as ex:
            raise DisplayableException(f"Update Test Case generation failed with reason: {ex}")

    def _generate_edits_for_test_element(
        self, test: XmlElement, input_params: List[XmlElement]
    ) -> List[ReplaceTextRangeResult]:
        test_params = test.get_children_with_name(PARAM)
        param_tree = self._build_param_ancestor_tree(test_params, input_params)
        edits = self._generate_xml_replacements_from_tree(param_tree)
        return edits

    def _generate_xml_replacements_from_tree(self, param_tree: ParameterNode) -> List[ReplaceTextRangeResult]:
        """Recursively builds the XML structure and generates replacement edits using the full hierarchy of test parameters."""

        def build_xml_recursive(node: ParameterNode, moved_params: Set[XmlElement]) -> Optional[etree._Element]:
            if not node.element:
                return None

            # Create an XML element for this (conditional, repeat, section) node
            ancestor_element = etree.Element(node.element.name or "")
            ancestor_element.attrib[NAME] = node.element.get_attribute_value(NAME) or ""

            # Add test parameters (direct children in XML)
            if node.test_parameters:
                for param in node.test_parameters:
                    param_element = self._to_etree(param)
                    ancestor_element.append(param_element)
                    moved_params.add(param)

            # Recursively add child elements
            for child in node.children:
                child_element = build_xml_recursive(child, moved_params)
                if child_element is not None:
                    ancestor_element.append(child_element)

            return ancestor_element

        result_edits: List[ReplaceTextRangeResult] = []
        # This is used to track which parameters have been moved to a new location
        # and should be removed from the original location
        moved_params: Set[XmlElement] = set()

        # Start building XML from the root node (skip adding the root itself since it’s virtual)
        for child in param_tree.children:
            ancestor_element = build_xml_recursive(child, moved_params)
            if ancestor_element is not None:
                ancestor_xml_text = etree.tostring(ancestor_element, pretty_print=True, encoding=str)

                # Find the location in the document to replace the first parameter
                first_param = child.test_parameters[0] if child.test_parameters else None
                if first_param:
                    first_param_range = self.tool_document.xml_document.get_element_range(first_param)
                    if first_param_range:
                        result_edits.append(ReplaceTextRangeResult(replace_range=first_param_range, text=ancestor_xml_text))
                        # Remove this parameter from the moved_params set since it has been processed
                        moved_params.discard(first_param)

        # Remove all parameters that were moved to a new location
        self._remove_params(moved_params, result_edits)

        return result_edits

    def _build_param_ancestor_tree(self, test_params: List[XmlElement], input_params: List[XmlElement]) -> ParameterNode:
        root = ParameterNode(name="root")
        for test_param in test_params:
            input_param = self._get_input_param_from_test_param(test_param, input_params)
            if input_param:
                ancestors = self._get_valid_ancestors(input_param)
                current_node = root
                for ancestor in ancestors:
                    key = self._get_element_key(ancestor)
                    existing_node = find_node_by_key(current_node, key)
                    if existing_node:
                        current_node = existing_node
                    else:
                        new_node = ParameterNode(name=key, parent=current_node, container_element=ancestor)
                        current_node = new_node
                if current_node.test_parameters is None:
                    current_node.test_parameters = []
                current_node.test_parameters.append(test_param)
        return root

    def _get_valid_ancestors(self, input_param: XmlElement) -> List[XmlElement]:
        ancestors = input_param.ancestors
        ancestors = [ancestor for ancestor in ancestors if self._is_valid_ancestor(ancestor)]
        return ancestors

    def _remove_params(self, params: Set[XmlElement], result_edits: List[ReplaceTextRangeResult]) -> None:
        for param in sorted(
            params, key=lambda p: self.tool_document.xml_document.get_element_range(p).start.line, reverse=True
        ):
            param_range = self.tool_document.xml_document.get_element_range(param)
            if param_range:
                result_edits.append(ReplaceTextRangeResult(replace_range=param_range, text=""))

    def _to_etree(self, param: XmlElement) -> etree._Element:
        param_element = etree.Element(PARAM)
        for attr_name, attr_value in param.attributes.items():
            param_element.attrib[attr_name] = attr_value.get_value()
        return param_element

    def _get_element_key(self, element: XmlElement) -> str:
        """Returns a string representation of the element key."""
        return f"{element.name}:{element.get_attribute_value(NAME) or ''}"

    def _is_valid_ancestor(self, element: Optional[XmlElement]) -> bool:
        """Checks if the element is a valid ancestor for grouping."""
        return element is not None and element.name in (CONDITIONAL, REPEAT, SECTION)

    def _get_input_param_from_test_param(self, test_param: XmlElement, input_params: List[XmlElement]) -> Optional[XmlElement]:
        """Returns the input parameter corresponding to the given test parameter."""
        name_attr = test_param.get_attribute_value(NAME)
        if name_attr:
            return next((p for p in input_params if p.get_attribute_value(NAME) == name_attr), None)
        return None
