import pytest
from pygls.types import Position, Range

from ...services.tools import GalaxyToolTestSnippetGenerator, GalaxyToolXmlDocument
from .sample_data import TEST_TOOL_WITH_INPUTS_DOCUMENT
from .utils import TestUtils


class TestGalaxyToolXmlDocumentClass:
    def test_init_sets_properties(self) -> None:
        document = TestUtils.to_document("<tool></tool>")
        tool = GalaxyToolXmlDocument(document)

        assert not tool.xml_document.is_empty

    @pytest.mark.parametrize(
        "source, expected",
        [
            ("", False),
            ("<macros>", False),
            ("<macros></macros>", False),
            ("<tool>", True),
            ("<tool></tool>", True),
        ],
    )
    def test_is_valid(self, source: str, expected: bool) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)

        assert tool.is_valid == expected

    def test_find_tests_section_without_section_returns_none(self) -> None:
        document = TestUtils.to_document("<tool></tool>")
        tool = GalaxyToolXmlDocument(document)

        actual = tool.find_element("notexistent")

        assert actual is None

    def test_find_tests_section_returns_expected(self) -> None:
        document = TestUtils.to_document("<tool><tests></tests></tool>")
        tool = GalaxyToolXmlDocument(document)

        actual = tool.find_element("tests")

        assert actual
        assert actual.name == "tests"

    def test_get_element_content_range_of_unknown_element_returns_none(self) -> None:
        document = TestUtils.to_document("<tool><tests></tests></tool>")
        tool = GalaxyToolXmlDocument(document)
        node = tool.find_element("unknown")

        actual = tool.get_element_content_range(node)

        assert actual is None

    @pytest.mark.parametrize(
        "source, element, expected",
        [
            ("<tool><tests/></tool>", "tests", None),
            ("<tool><tests></tests></tool>", "tests", Range(Position(0, 13), Position(0, 13))),
            ("<tool><tests>\n</tests></tool>", "tests", Range(Position(0, 13), Position(1, 0))),
            ("<tool>\n<tests>\n   \n</tests>\n</tool>", "tests", Range(Position(1, 7), Position(3, 0))),
            ("<tool>\n<tests>\n<test/></tests></tool>", "tests", Range(Position(1, 7), Position(2, 7))),
        ],
    )
    def test_get_element_content_range_of_element_returns_expected(self, source: str, element: str, expected: Range) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)
        node = tool.find_element(element)

        actual = tool.get_element_content_range(node)

        assert actual == expected

    @pytest.mark.parametrize(
        "source, expected",
        [
            ("", False),
            ("<macros>", False),
            ("<macros></macros>", False),
            ("<tool></tool>", False),
            ("<tool><macros></macros></tool>", False),
            ("<tool><expand/></tool>", True),
            ("<tool><expand></tool>", True),
            ("<tool><expand></expand></tool>", True),
            ("<tool><expand/><expand/></tool>", True),
        ],
    )
    def test_uses_macros_returns_expected(self, source: str, expected: bool) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)

        assert tool.uses_macros == expected

    def test_analyze_inputs_returns_expected_number_of_leaves(self) -> None:
        tool = GalaxyToolXmlDocument(TEST_TOOL_WITH_INPUTS_DOCUMENT)
        result = tool.analyze_inputs()

        assert len(result.leaves) == 3

    @pytest.mark.parametrize(
        "tool_file, expected_snippet_file",
        [
            ("simple_conditional_01.xml", "simple_conditional_01_test.xml"),
            ("simple_params_01.xml", "simple_params_01_test.xml"),
            ("simple_repeat_01.xml", "simple_repeat_01_test.xml"),
            ("simple_section_01.xml", "simple_section_01_test.xml"),
        ],
    )
    def test_generate_test_suite_snippet_returns_expected_result(self, tool_file: str, expected_snippet_file: str) -> None:
        document = TestUtils.get_test_document_from_file(tool_file)
        expected_snippet = TestUtils.get_test_file_contents(expected_snippet_file)
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolTestSnippetGenerator(tool)

        actual_snippet = generator.generate_test_suite_snippet()

        print(actual_snippet)

        assert actual_snippet == expected_snippet
