from typing import Optional
from pygls.types import Position

import pytest
from pygls.workspace import Document

from ....services.xml.nodes import XmlAttribute, XmlCDATASection, XmlElement
from ....services.xml.parser import XmlDocumentParser
from ....services.xml.types import DocumentType, NodeType
from ..sample_data import (
    TEST_MACRO_01_DOCUMENT,
    TEST_SYNTAX_ERROR_TOOL_01_DOCUMENT,
    TEST_TOOL_01_DOCUMENT,
    TEST_TOOL_WITH_PROLOG_DOCUMENT,
)
from ..utils import TestUtils


def assert_element_has_attribute(element: Optional[XmlElement], key: str, value: str) -> None:
    assert element
    assert element.attributes[key].key.name == key
    assert element.attributes[key].value.unquoted == value


def assert_element_has_offsets(element: Optional[XmlElement], start: int, end: int) -> None:
    assert element
    assert element.start == start
    assert element.end == end


def assert_attribute_has_offsets(attribute: Optional[XmlAttribute], start: int, end: int) -> None:
    assert attribute
    assert attribute.start == start
    assert attribute.end == end


def assert_attribute_has_key_offsets(attribute: Optional[XmlAttribute], start: int, end: int) -> None:
    assert attribute
    assert attribute.key
    assert attribute.key.start == start
    assert attribute.key.end == end


def assert_attribute_has_value_offsets(attribute: Optional[XmlAttribute], start: int, end: int) -> None:
    assert attribute
    assert attribute.value
    assert attribute.value.start == start
    assert attribute.value.end == end


class TestXmlDocumentParserClass:
    @pytest.mark.parametrize(
        "document, expected",
        [
            (TEST_TOOL_01_DOCUMENT, DocumentType.TOOL),
            (TEST_MACRO_01_DOCUMENT, DocumentType.MACROS),
            (TEST_SYNTAX_ERROR_TOOL_01_DOCUMENT, DocumentType.UNKNOWN),
        ],
    )
    def test_parse_returns_expected_document_type(self, document: Document, expected: DocumentType) -> None:
        parser = XmlDocumentParser()

        xml_document = parser.parse(document)

        assert xml_document.document_type == expected

    def test_parse_returns_expected_elements(self) -> None:
        test_document = TEST_TOOL_01_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert xml_document.root.name == "tool"
        assert len(xml_document.root.elements) == 4
        assert xml_document.root.elements[0].name == "command"
        assert xml_document.root.elements[1].name == "inputs"
        assert xml_document.root.elements[2].name == "outputs"
        assert xml_document.root.elements[3].name == "help"

    def test_parse_returns_expected_attributes(self) -> None:
        test_document = TEST_TOOL_01_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert len(xml_document.root.attributes) == 3
        assert xml_document.root.has_attributes
        assert_element_has_attribute(xml_document.root, "id", "test")
        assert_element_has_attribute(xml_document.root, "name", "Test Tool 01")
        assert_element_has_attribute(xml_document.root, "version", "0.1.0")
        assert len(xml_document.root.elements[0].attributes) == 1
        assert xml_document.root.elements[0].has_attributes
        assert_element_has_attribute(xml_document.root.elements[0], "detect_errors", "exit_code")
        assert not xml_document.root.elements[1].has_attributes
        assert not xml_document.root.elements[2].has_attributes
        assert not xml_document.root.elements[3].has_attributes

    def test_parse_returns_expected_attribute_offsets(self) -> None:
        test_document = TEST_TOOL_01_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert_attribute_has_offsets(xml_document.root.attributes["id"], 6, 15)
        assert_attribute_has_key_offsets(xml_document.root.attributes["id"], 6, 8)
        assert_attribute_has_value_offsets(xml_document.root.attributes["id"], 9, 15)
        assert_attribute_has_offsets(xml_document.root.attributes["name"], 16, 35)
        assert_attribute_has_key_offsets(xml_document.root.attributes["name"], 16, 20)
        assert_attribute_has_value_offsets(xml_document.root.attributes["name"], 21, 35)
        assert_attribute_has_offsets(xml_document.root.attributes["version"], 36, 51)
        assert_attribute_has_key_offsets(xml_document.root.attributes["version"], 36, 43)
        assert_attribute_has_value_offsets(xml_document.root.attributes["version"], 44, 51)

    def test_parse_returns_expected_element_offsets(self) -> None:
        test_document = TEST_TOOL_01_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert_element_has_offsets(xml_document.root, 0, 286)
        assert_element_has_offsets(xml_document.root.elements[0], 57, 159)
        assert_element_has_offsets(xml_document.root.elements[1], 164, 186)
        assert_element_has_offsets(xml_document.root.elements[2], 191, 215)
        assert_element_has_offsets(xml_document.root.elements[3], 220, 278)

    def test_parse_returns_expected_cdata_sections(self) -> None:
        test_document = TEST_TOOL_01_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert type(xml_document.root.elements[0].children[1]) is XmlCDATASection
        assert type(xml_document.root.elements[3].children[0]) is XmlCDATASection

    def test_parse_returns_expected_elements_when_macro(self) -> None:
        test_document = TEST_MACRO_01_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert xml_document.root.name == "macros"
        assert len(xml_document.root.elements) == 2
        assert xml_document.root.elements[0].name == "token"
        assert xml_document.root.elements[1].name == "macro"
        assert_element_has_attribute(xml_document.root.elements[1], "name", "inputs")
        assert xml_document.root.elements[1].elements[0].name == "inputs"
        assert xml_document.root.elements[1].elements[0].is_self_closed

    def test_parse_returns_expected_elements_when_has_prolog(self) -> None:
        test_document = TEST_TOOL_WITH_PROLOG_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert xml_document.root.name == "tool"
        assert len(xml_document.root.elements) == 2
        assert xml_document.root.elements[0].name == "inputs"
        assert xml_document.root.elements[1].name == "outputs"

    def test_parse_returns_expected_element_offsets_when_has_prolog(self) -> None:
        test_document = TEST_TOOL_WITH_PROLOG_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert_element_has_offsets(xml_document.root, 39, 125)
        assert_element_has_offsets(xml_document.root.elements[0], 93, 102)
        assert_element_has_offsets(xml_document.root.elements[1], 107, 117)

    @pytest.mark.parametrize(
        "source, expected",
        [
            ("", True),
            (" ", True),
            ("\n", True),
            (" \n ", True),
            (" \n text", True),
            ('<?xml version="1.0" encoding="UTF-8"?>', True),
            ("<", False),
            ("<tool", False),
            ("<tool ", False),
            ("<tool>", False),
            ('<?xml version="1.0" encoding="UTF-8"?><tool>', False),
        ],
    )
    def test_parse_empty_document_returns_is_empty(self, source: str, expected: bool) -> None:
        parser = XmlDocumentParser()
        document = TestUtils.to_document(source)
        xml_document = parser.parse(document)

        assert xml_document.is_empty == expected

    @pytest.mark.parametrize(
        "document, position, expected",
        [
            (TEST_TOOL_01_DOCUMENT, Position(0, 1), NodeType.ELEMENT),
            (TEST_TOOL_01_DOCUMENT, Position(0, 7), NodeType.ATTRIBUTE_KEY),
            (TEST_TOOL_01_DOCUMENT, Position(0, 8), NodeType.ATTRIBUTE_KEY),
            (TEST_TOOL_01_DOCUMENT, Position(0, 9), NodeType.ATTRIBUTE_VALUE),
            (TEST_TOOL_01_DOCUMENT, Position(0, 27), NodeType.ATTRIBUTE_VALUE),
            (TEST_TOOL_01_DOCUMENT, Position(1, 1), NodeType.CONTENT),
            (TEST_TOOL_01_DOCUMENT, Position(1, 44), NodeType.CDATA_SECTION),
            (TEST_TOOL_01_DOCUMENT, Position(2, 0), NodeType.CDATA_SECTION),
            (TEST_TOOL_01_DOCUMENT, Position(3, 6), NodeType.CDATA_SECTION),
            (TEST_TOOL_01_DOCUMENT, Position(3, 7), NodeType.CONTENT),
            (TEST_TOOL_01_DOCUMENT, Position(3, 8), NodeType.ELEMENT),
        ],
    )
    def test_get_node_at_returns_expected_type(self, document: Document, position: Position, expected: NodeType) -> None:
        parser = XmlDocumentParser()
        xml_document = parser.parse(document)
        offset = document.offset_at_position(position)

        actual = xml_document.get_node_at(offset)

        assert actual.node_type == expected

    @pytest.mark.parametrize(
        "source, expected",
        [
            ("", True),
            (" ", True),
            ("\n", True),
            (" \n ", True),
            (" \n text", True),
            ('<?xml version="1.0" encoding="UTF-8"?>', True),
            ("<", True),
            ("<tool", False),
            ("<macros", False),
            ("<tool ", False),
            ("<macros ", False),
            ("<tool>", False),
            ("<macros>", False),
            ('<?xml version="1.0" encoding="UTF-8"?><tool>', False),
            ('<?xml version="1.0" encoding="UTF-8"?><macros>', False),
        ],
    )
    def test_parse_document_returns_expected_is_unknown(self, source: str, expected: bool) -> None:
        parser = XmlDocumentParser()
        document = TestUtils.to_document(source)
        xml_document = parser.parse(document)

        assert xml_document.is_unknown == expected

    @pytest.mark.parametrize(
        "source, expected",
        [
            ("", False),
            (" ", False),
            ("\n", False),
            (" \n ", False),
            (" \n text", False),
            ('<?xml version="1.0" encoding="UTF-8"?>', False),
            ("<", False),
            ("<tool", False),
            ("<macro", False),
            ("<macros", True),
            ("<tool ", False),
            ("<macros ", True),
            ("<tool>", False),
            ("<macros>", True),
            ('<?xml version="1.0" encoding="UTF-8"?><tool>', False),
            ('<?xml version="1.0" encoding="UTF-8"?><macros>', True),
        ],
    )
    def test_parse_document_returns_expected_is_macros_file(self, source: str, expected: bool) -> None:
        parser = XmlDocumentParser()
        document = TestUtils.to_document(source)
        xml_document = parser.parse(document)

        assert xml_document.is_macros_file == expected
