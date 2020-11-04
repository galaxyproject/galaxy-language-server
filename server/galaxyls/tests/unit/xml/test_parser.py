from typing import Optional

import pytest
from pygls.workspace import Document

from ....services.xml.nodes import XmlAttribute, XmlCDATASection, XmlElement
from ....services.xml.parser import XmlDocumentParser
from ....services.xml.types import DocumentType
from ..sample_data import (
    TEST_MACRO_01_DOCUMENT,
    TEST_SYNTAX_ERROR_TOOL_01_DOCUMENT,
    TEST_TOOL_01_DOCUMENT,
    TEST_TOOL_WITH_PROLOG_DOCUMENT,
)


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
    def test_parse_returns_expected_document_type(self, document: Document, expected: DocumentType):
        parser = XmlDocumentParser()

        xml_document = parser.parse(document)

        assert xml_document.document_type == expected

    def test_parse_returns_expected_elements(self):
        test_document = TEST_TOOL_01_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert xml_document.root.name == "tool"
        assert len(xml_document.root.elements) == 4
        assert xml_document.root.elements[0].name == "command"
        assert xml_document.root.elements[1].name == "inputs"
        assert xml_document.root.elements[2].name == "outputs"
        assert xml_document.root.elements[3].name == "help"

    def test_parse_returns_expected_attributes(self):
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

    def test_parse_returns_expected_attribute_offsets(self):
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

    def test_parse_returns_expected_element_offsets(self):
        test_document = TEST_TOOL_01_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert_element_has_offsets(xml_document.root, 0, 286)
        assert_element_has_offsets(xml_document.root.elements[0], 57, 159)
        assert_element_has_offsets(xml_document.root.elements[1], 164, 186)
        assert_element_has_offsets(xml_document.root.elements[2], 191, 215)
        assert_element_has_offsets(xml_document.root.elements[3], 220, 278)

    def test_parse_returns_expected_cdata_sections(self):
        test_document = TEST_TOOL_01_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert type(xml_document.root.elements[0].children[0]) is XmlCDATASection
        assert type(xml_document.root.elements[3].children[0]) is XmlCDATASection

    def test_parse_returns_expected_elements_when_macro(self):
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

    def test_parse_returns_expected_elements_when_has_prolog(self):
        test_document = TEST_TOOL_WITH_PROLOG_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert xml_document.root.name == "tool"
        assert len(xml_document.root.elements) == 2
        assert xml_document.root.elements[0].name == "inputs"
        assert xml_document.root.elements[1].name == "outputs"

    def test_parse_returns_expected_element_offsets_when_has_prolog(self):
        test_document = TEST_TOOL_WITH_PROLOG_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert_element_has_offsets(xml_document.root, 39, 125)
        assert_element_has_offsets(xml_document.root.elements[0], 93, 102)
        assert_element_has_offsets(xml_document.root.elements[1], 107, 117)
