import pytest
from lxml import etree

from galaxyls.services.validation import DocumentValidator
from ...services.xsd.constants import TOOL_XSD_FILE
from ...services.xsd.validation import GalaxyToolSchemaValidationService
from .sample_data import (
    TEST_MACRO_01_DOCUMENT,
    TEST_SYNTAX_ERROR_MACRO_01_DOCUMENT,
    TEST_SYNTAX_ERROR_TOOL_01_DOCUMENT,
)
from .utils import TestUtils


@pytest.fixture(scope="module")
def xsd_schema() -> etree.XMLSchema:
    root = etree.parse(str(TOOL_XSD_FILE))
    schema = etree.XMLSchema(root)
    return schema


class TestGalaxyToolValidationServiceClass:
    def test_validate_document_returns_empty_diagnostics_when_valid(self, xsd_schema: etree.XMLSchema) -> None:
        service = GalaxyToolSchemaValidationService(xsd_schema)
        xml_document = TestUtils.get_test_xml_document_from_file("test_tool_01.xml")

        actual = service.validate_document(xml_document)

        assert actual == []

    def test_validate_macro_file_returns_empty_diagnostics_when_valid(self, xsd_schema: etree.XMLSchema) -> None:
        service = GalaxyToolSchemaValidationService(xsd_schema)
        xml_document = TestUtils.from_document_to_xml_document(TEST_MACRO_01_DOCUMENT)

        actual = service.validate_document(xml_document)

        assert actual == []

    def test_validate_document_returns_diagnostics_when_invalid(self, xsd_schema: etree.XMLSchema) -> None:
        service = GalaxyToolSchemaValidationService(xsd_schema)
        xml_document = TestUtils.get_test_xml_document_from_file("test_invalid_tool_01.xml")

        actual = service.validate_document(xml_document)

        assert len(actual) > 0

    def test_validate_document_returns_diagnostics_when_syntax_error(self, xsd_schema: etree.XMLSchema) -> None:
        service = GalaxyToolSchemaValidationService(xsd_schema)
        xml_document = TestUtils.from_document_to_xml_document(TEST_SYNTAX_ERROR_TOOL_01_DOCUMENT)

        actual = service.validate_document(xml_document)

        assert len(actual) == 1

    def test_validate_macro_file_returns_diagnostics_when_syntax_error(self, xsd_schema: etree.XMLSchema) -> None:
        service = GalaxyToolSchemaValidationService(xsd_schema)
        xml_document = TestUtils.from_document_to_xml_document(TEST_SYNTAX_ERROR_MACRO_01_DOCUMENT)

        actual = service.validate_document(xml_document)

        assert len(actual) == 1


class TestDocumentValidatorClass:
    @pytest.mark.parametrize(
        "source, expected",
        [
            ("<", True),
            ("", True),
            ("   ", True),
            ("  \n ", True),
            ("<tool>", True),
            ("  <tool>", True),
            ("\n<tool>", True),
            ("\n  <tool>", True),
            ("  \n  <tool>", True),
            ("unexpected  <tool>", True),
            ("  unexpected  <tool>", True),
            ("\nunexpected\n  <tool>", True),
            ('<?xml version="1.0" encoding="UTF-8"?><tool>', True),
            ('<?xml version="1.0" encoding="UTF-8"?>\n<tool>', True),
            ("<macros>", True),
            ('<?xml version="1.0" encoding="UTF-8"?>\n<macros>', True),
            ("test", False),
            ("<test>", False),
        ],
    )
    def test_has_valid_root_returns_expected(self, source: str, expected: bool) -> None:
        document = TestUtils.to_document(source)
        validator = DocumentValidator()

        actual = validator.has_valid_root(document)

        assert actual == expected
