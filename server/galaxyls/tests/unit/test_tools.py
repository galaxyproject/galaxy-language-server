from pygls.types import Position, Range
import pytest
from ...services.tools import GalaxyToolXmlDocument
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
        ],
    )
    def test_uses_macros_returns_expected(self, source: str, expected: bool) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)

        assert tool.uses_macros == expected
