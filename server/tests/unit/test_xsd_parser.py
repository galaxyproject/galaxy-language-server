import pytest

from typing import List
from lxml import etree

from .sample_data import TEST_XSD, RECURSIVE_XSD
from ...services.xsd.parser import GalaxyToolXsdParser
from ...services.xsd.constants import MSG_NO_DOCUMENTATION_AVAILABLE


@pytest.fixture(scope="module")
def xsd_parser() -> GalaxyToolXsdParser:
    root = etree.fromstring(TEST_XSD)
    parser = GalaxyToolXsdParser(root)
    return parser


@pytest.fixture(scope="module")
def recursive_xsd_parser() -> GalaxyToolXsdParser:
    root = etree.fromstring(RECURSIVE_XSD)
    parser = GalaxyToolXsdParser(root)
    return parser


class TestXsdParserClass:
    def test_get_tree_returns_valid_element_names(self, xsd_parser: GalaxyToolXsdParser) -> None:
        tree = xsd_parser.get_tree()
        root = tree.root

        # If the test fails the tree will be printed
        print(tree.render())

        assert len(root.ancestors) == 0
        assert len(root.descendants) == 10
        assert root.name == "testElement"
        assert root.children[0].name == "firstElement"
        assert root.children[1].name == "secondElement"
        assert root.children[1].children[0].name == "group_elem1"
        assert root.children[1].children[1].name == "group_elem2"
        assert root.children[1].children[2].name == "content"
        assert root.children[2].name == "thirdElement"
        assert root.children[2].children[0].name == "childElement"
        assert root.children[3].name == "element_with_group"
        assert root.children[3].children[0].name == "group_elem1"
        assert root.children[3].children[1].name == "group_elem2"

    def test_get_tree_returns_valid_attribute_names_using_groups(
        self, xsd_parser: GalaxyToolXsdParser
    ) -> None:
        tree = xsd_parser.get_tree()
        root = tree.root

        assert len(root.attributes) == 4
        assert root.attributes["id"]
        assert root.attributes["value"]
        assert root.attributes["gattr1"]
        assert root.attributes["gattr2"]

    def test_get_tree_returns_valid_attribute_names_when_simple_content(
        self, xsd_parser: GalaxyToolXsdParser
    ) -> None:
        tree = xsd_parser.get_tree()
        simple_content_elem = tree.root.children[2].children[0]

        assert len(simple_content_elem.attributes) == 1
        assert simple_content_elem.attributes["simple"]

    def test_get_tree_returns_valid_element_when_complex_content(
        self, xsd_parser: GalaxyToolXsdParser
    ) -> None:
        tree = xsd_parser.get_tree()
        complex_content_elem = tree.root.children[2].children[0]

        assert len(complex_content_elem.attributes) == 1
        assert complex_content_elem.attributes["simple"]

    def test_get_tree_with_recursive_xsd_stops_recursion(
        self, recursive_xsd_parser: GalaxyToolXsdParser
    ) -> None:
        tree = recursive_xsd_parser.get_tree()

        assert len(tree.root.descendants) > 0

    def test_tree_find_node_by_name_returns_expected_node(
        self, xsd_parser: GalaxyToolXsdParser
    ) -> None:
        tree = xsd_parser.get_tree()
        expected = "childElement"

        node = tree.find_node_by_name(expected)

        assert node.name == expected

    @pytest.mark.parametrize(
        "stack, expected",
        [
            (["testElement"], "testElement",),
            (["testElement", "firstElement"], "firstElement",),
            (["testElement", "secondElement"], "secondElement",),
            (["testElement", "secondElement", "group_elem1"], "group_elem1",),
            (["testElement", "element_with_group", "group_elem1"], "group_elem1",),
        ],
    )
    def test_tree_find_node_by_stack_returns_expected_node(
        self, xsd_parser: GalaxyToolXsdParser, stack: List[str], expected: str
    ) -> None:
        tree = xsd_parser.get_tree()

        node = tree.find_node_by_stack(stack)

        assert node.name == expected

    def test_tree_find_node_by_name_returns_None_when_node_not_found(
        self, xsd_parser: GalaxyToolXsdParser
    ) -> None:
        tree = xsd_parser.get_tree()

        node = tree.find_node_by_name("unknown")

        assert node is None

    def test_get_documentation_returns_valid_when_exists(
        self, xsd_parser: GalaxyToolXsdParser
    ) -> None:
        tree = xsd_parser.get_tree()

        doc = tree.root.get_doc()

        assert doc.value == "Documentation ``example``."

    def test_get_documentation_returns_valid_other_language(
        self, xsd_parser: GalaxyToolXsdParser
    ) -> None:
        tree = xsd_parser.get_tree()

        doc = tree.root.get_doc("es")

        assert doc.value == "``Ejemplo`` de documentación."

    def test_get_documentation_should_return_no_documentation_when_not_exists(
        self, xsd_parser: GalaxyToolXsdParser
    ) -> None:
        tree = xsd_parser.get_tree()

        doc = tree.root.get_doc("de")

        assert doc.value == MSG_NO_DOCUMENTATION_AVAILABLE

    def test_parser_returns_expected_enumeration_restrictions(
        self, xsd_parser: GalaxyToolXsdParser
    ) -> None:
        tree = xsd_parser.get_tree()

        attribute_with_restriction = tree.root.attributes["value"]
        actual = attribute_with_restriction.enumeration

        assert actual == ["v1", "v2", "v3"]

    def test_parser_returns_expected_occurs_restrictions(
        self, xsd_parser: GalaxyToolXsdParser
    ) -> None:
        tree = xsd_parser.get_tree()

        actual = tree.root

        assert actual.min_occurs == 1
        assert actual.max_occurs == 1

    def test_parser_returns_expected_occurs_when_unbounded(
        self, xsd_parser: GalaxyToolXsdParser
    ) -> None:
        tree = xsd_parser.get_tree()

        actual = tree.root.children[0]

        assert actual.min_occurs == 0
        assert actual.max_occurs == -1
