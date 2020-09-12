import pytest
from pytest_mock import MockerFixture
from pygls.workspace import Document, Position

from ...services.context import XmlContextService, XmlContext, XmlContextParser, ContextTokenType


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


def print_context_params(document: Document, position: Position):
    print(f"Test context at position [line={position.line}, char={position.character}]")
    print(f"Document:\n{document.source}")


class TestXmlContextClass:
    def test_init_sets_properties(self) -> None:
        expected_line_content = "test"
        expected_position = Position()

        context = XmlContext(document_line=expected_line_content, position=expected_position)

        assert context.document_line == expected_line_content
        assert context.target_position == expected_position
        assert not context.is_empty

    def test_context_with_unknown_token_type_returns_all_false(self) -> None:
        context = XmlContext(token_type=ContextTokenType.UNKNOWN)

        assert not context.is_tag()
        assert not context.is_attribute_key()
        assert not context.is_attribute_value()

    def test_context_with_tag_token_type_returns_is_tag(self) -> None:
        context = XmlContext(token_type=ContextTokenType.TAG)

        assert context.is_tag()
        assert not context.is_attribute_key()
        assert not context.is_attribute_value()

    def test_context_with_attr_key_token_type_returns_is_attr_key(self) -> None:
        context = XmlContext(token_type=ContextTokenType.ATTRIBUTE_KEY)

        assert not context.is_tag()
        assert context.is_attribute_key()
        assert not context.is_attribute_value()

    def test_context_with_attr_value_token_type_returns_is_attr_value(self) -> None:
        context = XmlContext(token_type=ContextTokenType.ATTRIBUTE_VALUE)

        assert not context.is_tag()
        assert not context.is_attribute_key()
        assert context.is_attribute_value()


class TestXmlContextServiceClass:
    def test_init_sets_properties(self, mocker: MockerFixture) -> None:
        expected = mocker.Mock()

        service = XmlContextService(expected)

        assert service.xsd_tree

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


class TestXmlContextParserClass:
    @pytest.mark.parametrize(
        "document, position, expected",
        [
            (FAKE_DOCUMENT, Position(line=1, character=0), None),
            (FAKE_DOCUMENT, Position(line=1, character=1), "tool"),
            (FAKE_DOCUMENT, Position(line=1, character=5), "tool"),
            (FAKE_DOCUMENT, Position(line=1, character=6), "id"),
            (FAKE_DOCUMENT, Position(line=1, character=8), "id"),
            (FAKE_DOCUMENT, Position(line=1, character=9), None),
            (FAKE_DOCUMENT, Position(line=1, character=10), "test"),
            (FAKE_DOCUMENT, Position(line=1, character=14), "test"),
            (FAKE_DOCUMENT, Position(line=1, character=15), None),
            (FAKE_DOCUMENT, Position(line=2, character=5), "description"),
            (FAKE_DOCUMENT, Position(line=2, character=16), "description"),
            (FAKE_DOCUMENT, Position(line=2, character=17), None),
            (FAKE_DOCUMENT, Position(line=3, character=4), None),
            (FAKE_DOCUMENT, Position(line=3, character=5), "test"),
            (FAKE_DOCUMENT, Position(line=3, character=9), "test"),
            (FAKE_DOCUMENT, Position(line=3, character=10), "value"),
            (FAKE_DOCUMENT, Position(line=3, character=15), "value"),
            (FAKE_DOCUMENT, Position(line=3, character=16), None),
            (FAKE_DOCUMENT, Position(line=3, character=17), "0"),
            (FAKE_DOCUMENT, Position(line=3, character=18), "0"),
            (FAKE_DOCUMENT, Position(line=3, character=19), None),
        ],
    )
    def test_parse_well_formed_xml_return_expected_context_token_name(
        self, document: Document, position: Position, expected: str
    ) -> None:
        print_context_params(document, position)
        parser = XmlContextParser()

        context = parser.parse(document, position)

        assert context.token_name == expected

    @pytest.mark.parametrize(
        "document, position, expected",
        [
            (get_fake_document('<other id="1"'), Position(line=0, character=0), None),
            (get_fake_document('<other id="1"'), Position(line=0, character=1), "other"),
            (get_fake_document('<other id="1"'), Position(line=0, character=6), "other"),
            (get_fake_document('<other id="1"'), Position(line=0, character=7), "id"),
            (get_fake_document('<other id="1"'), Position(line=0, character=9), "id"),
            (get_fake_document('<other id="1"'), Position(line=0, character=11), "1"),
            (get_fake_document('<other id="1"'), Position(line=0, character=12), "1"),
            (get_fake_document('<other id="1"'), Position(line=0, character=13), None),
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
            (
                get_fake_document('<first id="one_test">\n    <second'),
                Position(line=0, character=11),
                "one_test",
            ),
            (
                get_fake_document('<first id="one_test">\n    <second'),
                Position(line=0, character=19),
                "one_test",
            ),
            (
                get_fake_document('<first id="one test">\n    <second'),
                Position(line=0, character=11),
                "one test",
            ),
            (
                get_fake_document('<first id="one test">\n    <second'),
                Position(line=0, character=19),
                "one test",
            ),
            (
                get_fake_document('<first id="one test'),
                Position(line=0, character=19),
                "one test",
            ),
        ],
    )
    def test_parse_incomplete_xml_return_expected_context_token_name(
        self, document: Document, position: Position, expected: str
    ) -> None:
        print_context_params(document, position)
        parser = XmlContextParser()

        context = parser.parse(document, position)

        assert context.token_name == expected

    @pytest.mark.parametrize(
        "document, position, expected",
        [
            (
                get_fake_document('<first id="1" test="value">\n    <second'),
                Position(line=0, character=0),
                ContextTokenType.UNKNOWN,
            ),
            (
                get_fake_document('<first id="1" test="value">\n    <second'),
                Position(line=0, character=2),
                ContextTokenType.TAG,
            ),
            (
                get_fake_document('<first id="1" test="value">\n    <second'),
                Position(line=0, character=8),
                ContextTokenType.ATTRIBUTE_KEY,
            ),
            (
                get_fake_document('<first id="1" test="value">\n    <second'),
                Position(line=0, character=11),
                ContextTokenType.ATTRIBUTE_VALUE,
            ),
            (
                get_fake_document('<first id="one_test">\n    <second'),
                Position(line=0, character=19),
                ContextTokenType.ATTRIBUTE_VALUE,
            ),
            (
                get_fake_document('<first id="one test'),
                Position(line=0, character=19),
                ContextTokenType.ATTRIBUTE_VALUE,
            ),
        ],
    )
    def test_parse_incomplete_xml_return_expected_context_token_type(
        self, document: Document, position: Position, expected: str
    ) -> None:
        print_context_params(document, position)
        parser = XmlContextParser()

        context = parser.parse(document, position)

        assert context.token_type == expected

    @pytest.mark.parametrize(
        "document, position, expected",
        [
            (get_fake_document(""), Position(line=0, character=0), True),
            (get_fake_document(""), Position(line=0, character=10), True),
            (get_fake_document("<"), Position(line=0, character=0), True),
            (get_fake_document("   "), Position(line=0, character=0), True),
            (get_fake_document("\n\n"), Position(line=0, character=0), True),
            (get_fake_document("\n\n"), Position(line=1, character=0), True),
        ],
    )
    def test_parse_empty_xml_return_empty_context(
        self, document: Document, position: Position, expected: bool
    ) -> None:
        print_context_params(document, position)
        parser = XmlContextParser()

        context = parser.parse(document, position)

        assert context.is_empty == expected

    @pytest.mark.parametrize(
        "document, position, expected",
        [
            (
                get_fake_document("<first><second><third>"),
                Position(line=0, character=1),
                ["first"],
            ),
            (
                get_fake_document("<first><second><third>"),
                Position(line=0, character=8),
                ["first", "second"],
            ),
            (
                get_fake_document("<first><second><third>"),
                Position(line=0, character=16),
                ["first", "second", "third"],
            ),
            (
                get_fake_document("<first><second/><third>"),
                Position(line=0, character=17),
                ["first", "third"],
            ),
        ],
    )
    def test_parse_return_valid_tag_stack_context(
        self, document: Document, position: Position, expected: bool
    ) -> None:
        print_context_params(document, position)
        parser = XmlContextParser()

        context = parser.parse(document, position)

        assert context.node_stack == expected

    @pytest.mark.parametrize(
        "document, position, expected",
        [
            (
                get_fake_document(
                    '<first id="1">\n    <second attr="value">test</second>\n<third'
                ),
                Position(line=0, character=1),
                False,
            ),
            (
                get_fake_document(
                    '<first id="1">\n    <second attr="value">test</second>\n<third'
                ),
                Position(line=0, character=8),
                False,
            ),
            (
                get_fake_document(
                    '<first id="1">\n    <second attr="value">test</second>\n<third'
                ),
                Position(line=0, character=14),
                True,
            ),
            (
                get_fake_document(
                    '<first id="1">\n    <second attr="value">test</second>\n<third'
                ),
                Position(line=1, character=0),
                True,
            ),
            (
                get_fake_document(
                    '<first id="1">\n    <second attr="value">test</second>\n<third'
                ),
                Position(line=1, character=4),
                True,
            ),
            (
                get_fake_document(
                    '<first id="1">\n    <second attr="value">test</second>\n<third'
                ),
                Position(line=1, character=5),
                False,
            ),
            (
                get_fake_document(
                    '<first id="1">\n    <second attr="value">test</second>\n<third'
                ),
                Position(line=1, character=6),
                False,
            ),
            (
                get_fake_document(
                    '<first id="1">\n    <second attr="value">test</second>\n<third'
                ),
                Position(line=1, character=24),
                False,
            ),
            (
                get_fake_document(
                    '<first id="1">\n    <second attr="value">test</second>\n<third'
                ),
                Position(line=1, character=25),
                True,
            ),
            (
                get_fake_document(
                    '<first id="1">\n    <second attr="value">test</second>\n<third'
                ),
                Position(line=1, character=29),
                True,
            ),
            (
                get_fake_document(
                    '<first id="1">\n    <second attr="value">test</second>\n<third'
                ),
                Position(line=1, character=30),
                False,
            ),
        ],
    )
    def test_parse_returns_context_with_expected_is_node_content(
        self, document: Document, position: Position, expected: bool
    ) -> None:
        print_context_params(document, position)
        parser = XmlContextParser()

        context = parser.parse(document, position)

        assert context.is_node_content == expected
