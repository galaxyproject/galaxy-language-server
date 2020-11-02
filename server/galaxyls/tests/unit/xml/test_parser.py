from typing import Optional
from pygls.workspace import Document

import pytest

from ....services.xml.nodes import XmlCDATASection, XmlElement
from ....services.xml.parser import XmlDocumentParser
from ....services.xml.types import DocumentType
from ..sample_data import TEST_MACRO_01_DOCUMENT, TEST_TOOL_01_DOCUMENT


def element_has_attribute(element: Optional[XmlElement], key: str, value: str) -> bool:
    return element is not None and element.attributes[key].key.name == key and element.attributes[key].value.unquoted == value


def element_has_offsets(element: Optional[XmlElement], start: int, end: int) -> bool:
    return element is not None and element.start == start and element.end == end


class TestXmlDocumentParserClass:
    @pytest.mark.parametrize(
        "document, expected",
        [
            (
                TEST_TOOL_01_DOCUMENT,
                DocumentType.TOOL,
            ),
            (
                TEST_MACRO_01_DOCUMENT,
                DocumentType.MACROS,
            ),
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

        assert xml_document.document_type == DocumentType.TOOL
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
        assert element_has_attribute(xml_document.root, "id", "test")
        assert element_has_attribute(xml_document.root, "name", "Test Tool 01")
        assert element_has_attribute(xml_document.root, "version", "0.1.0")
        assert element_has_attribute(xml_document.root.elements[0], "detect_errors", "exit_code")

    def test_parse_returns_expected_element_offsets(self):
        test_document = TEST_TOOL_01_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert element_has_offsets(xml_document.root, 0, 286)
        assert element_has_offsets(xml_document.root.elements[0], 57, 159)
        assert element_has_offsets(xml_document.root.elements[1], 164, 186)
        assert element_has_offsets(xml_document.root.elements[2], 191, 215)
        assert element_has_offsets(xml_document.root.elements[3], 220, 278)

    def test_parse_returns_expected_cdata_sections(self):
        test_document = TEST_TOOL_01_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert type(xml_document.root.elements[0].children[0]) is XmlCDATASection
        assert type(xml_document.root.elements[3].children[0]) is XmlCDATASection
