import pytest
from pytest_mock import MockerFixture

from ...services.context import (
    XmlContextService,
    XmlContext,
    XmlContextParser,
)

from pygls.workspace import Document, Position

# The content starts at line 1 for convenience
FAKE_CONTENT = """
<tool id="test">
    <description/>
    <test value="0"/>
</tool>'
"""
FAKE_DOC_URI = "file://fake_doc.xml"
FAKE_DOCUMENT = Document(FAKE_DOC_URI, FAKE_CONTENT)


def get_fake_document(content: str):
    return Document(FAKE_DOC_URI, content)


class TestXmlContextClass:
    def test_init_sets_properties(self, mocker: MockerFixture) -> None:
        expected_name = "test"
        expected_node = mocker.Mock()

        context = XmlContext(expected_name, expected_node)

        assert context.token_name == expected_name
        assert context.node == expected_node


class TestXmlContextServiceClass:
    def test_init_sets_properties(self, mocker: MockerFixture) -> None:
        expected = mocker.Mock()

        service = XmlContextService(expected)

        assert service.xsd_tree

    @pytest.mark.parametrize(
        "document, position, expected",
        [
            (FAKE_DOCUMENT, Position(line=1, character=4), "tool"),
            (FAKE_DOCUMENT, Position(line=1, character=8), "tool"),
            (FAKE_DOCUMENT, Position(line=2, character=0), "tool"),
            (FAKE_DOCUMENT, Position(line=3, character=0), "tool"),
            (FAKE_DOCUMENT, Position(line=3, character=21), "tool"),
            (FAKE_DOCUMENT, Position(line=4, character=0), "tool"),
            (FAKE_DOCUMENT, Position(line=2, character=5), "description"),
            (FAKE_DOCUMENT, Position(line=2, character=17), "description"),
            (FAKE_DOCUMENT, Position(line=3, character=5), "test"),
            (FAKE_DOCUMENT, Position(line=3, character=12), "test"),
            (FAKE_DOCUMENT, Position(line=3, character=17), "test"),
        ],
    )
    def test_get_current_tag_at_position_is_expected(
        self, document: Document, position: Position, expected: str
    ) -> None:
        offset = document.offset_at_position(position)

        actual = XmlContextService.find_current_tag(document.source, offset)

        assert actual == expected

    def test_get_current_tag_returns_none_when_empty_document(self) -> None:
        xml_content = ""
        offset = 0

        actual = XmlContextService.find_current_tag(xml_content, offset)

        assert actual is None

    def test_get_xml_context_returns_empty_document_context(self, mocker: MockerFixture) -> None:
        xml_content = ""
        position = Position()
        xsd_tree_mock = mocker.Mock()
        service = XmlContextService(xsd_tree_mock)

        context = service.get_xml_context(Document(FAKE_DOC_URI, xml_content), position)

        assert context.is_empty

    def test_get_xml_context_returns_valid_context_with_node(self, mocker: MockerFixture,) -> None:
        xsd_tree_mock = mocker.Mock()
        expected_element = "test"
        xml_content = f"<{expected_element}>"
        position = Position(line=0, character=3)
        service = XmlContextService(xsd_tree_mock)

        context = service.get_xml_context(Document(FAKE_DOC_URI, xml_content), position)

        assert context
        assert context.node
        assert context.token_name == expected_element

    def test_get_xml_context_returns_valid_context_without_node(
        self, mocker: MockerFixture,
    ) -> None:
        xsd_tree_mock = mocker.Mock()
        xml_content = "content with no tags"
        position = Position(line=0, character=3)
        service = XmlContextService(xsd_tree_mock)

        context = service.get_xml_context(Document(FAKE_DOC_URI, xml_content), position)

        assert context
        assert context.node is None
        assert context.token_name is None

    @pytest.mark.parametrize(
        "xml_content, expected",
        [
            (get_fake_document(""), True),
            (get_fake_document("<"), True),
            (get_fake_document(" "), True),
            (get_fake_document("   "), True),
            (get_fake_document("\r\n"), True),
            (get_fake_document("\r"), True),
            (get_fake_document(" \r"), True),
            (get_fake_document("\n"), True),
            (get_fake_document(" \n"), True),
            (get_fake_document("<a"), False),
            (get_fake_document("<test"), False),
        ],
    )
    def test_is_empty_content_returns_empty_document_context(
        self, xml_content: str, expected: bool
    ) -> None:
        actual = XmlContextService.is_empty_content(xml_content)

        assert actual == expected

    @pytest.mark.parametrize(
        "xml_content, offset, expected",
        [
            ("<test", 0, None),
            ("<test", 1, "test"),
            ("<test\n", 1, "test"),
            ("<test ", 1, "test"),
            ("<test>\n", 6, "test"),
            ("<test/>\n", 7, None),
            ("<test><other>\n", 7, "other"),
            ("<test><other/>\n", 14, "test"),
            ("<test>\r\n<other/>\n", 17, "test"),
        ],
    )
    def test_find_current_tag_returns_expected_tag(
        self, xml_content: str, offset: int, expected: str,
    ) -> None:
        actual = XmlContextService.find_current_tag(xml_content, offset)

        assert actual == expected


class TestXmlContextParserClass:
    @pytest.mark.parametrize(
        "document, position, expected",
        [
            (FAKE_DOCUMENT, Position(line=1, character=4), "tool"),
            (FAKE_DOCUMENT, Position(line=1, character=8), "id"),
            (FAKE_DOCUMENT, Position(line=1, character=10), "test"),
            (FAKE_DOCUMENT, Position(line=2, character=5), "description"),
            (FAKE_DOCUMENT, Position(line=2, character=17), None),
            (FAKE_DOCUMENT, Position(line=3, character=5), "test"),
            (FAKE_DOCUMENT, Position(line=3, character=12), "value"),
            (FAKE_DOCUMENT, Position(line=3, character=17), "0"),
        ],
    )
    def test_parse_well_formed_xml_return_expected_context_token_name(
        self, document: Document, position: Position, expected: str
    ) -> None:
        parser = XmlContextParser()

        context = parser.parse(document, position)

        assert context.token_name == expected

    @pytest.mark.parametrize(
        "document, position, expected",
        [
            (get_fake_document('<other id="1"'), Position(line=0, character=2), "other"),
            (get_fake_document('<other id="1"'), Position(line=0, character=7), "id"),
            (get_fake_document('<other id="1"'), Position(line=0, character=11), "1"),
            (
                get_fake_document('<first id="1" test="value">\n    <second'),
                Position(line=0, character=2),
                "first",
            ),
            (
                get_fake_document('<first id="1" test="value">\n    <second'),
                Position(line=0, character=8),
                "id",
            ),
            (
                get_fake_document('<first id="1" test="value">\n    <second'),
                Position(line=0, character=11),
                "1",
            ),
            (
                get_fake_document('<first id="1" test="value">\n    <second'),
                Position(line=0, character=12),
                "1",
            ),
            (
                get_fake_document('<first id="1" test="value">\n    <second'),
                Position(line=0, character=14),
                "test",
            ),
            (
                get_fake_document('<first id="1" test="value">\n    <second'),
                Position(line=0, character=20),
                "value",
            ),
            (
                get_fake_document('<first id="1" test="value">\n    <second'),
                Position(line=0, character=25),
                "value",
            ),
            (
                get_fake_document('<first id="1" test="value">\n    <second'),
                Position(line=1, character=5),
                "second",
            ),
        ],
    )
    def test_parse_incomplete_xml_return_expected_context_token_name(
        self, document: Document, position: Position, expected: str
    ) -> None:
        parser = XmlContextParser()

        context = parser.parse(document, position)

        assert context.token_name == expected


# <tool id="test">
#     <description/>
#     <test value="0"/>
# </tool>'
