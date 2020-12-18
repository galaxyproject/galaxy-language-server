import pytest
from lxml import etree

from ...services.xsd.constants import TOOL_XSD_FILE
from ...services.xsd.validation import GalaxyToolValidationService
from .sample_data import (
    TEST_INVALID_TOOL_01_DOCUMENT,
    TEST_MACRO_01_DOCUMENT,
    TEST_SYNTAX_ERROR_MACRO_01_DOCUMENT,
    TEST_SYNTAX_ERROR_TOOL_01_DOCUMENT,
    TEST_TOOL_01_DOCUMENT,
)
from .utils import TestUtils

TEST_SERVER_NAME = "Test Server"


@pytest.fixture(scope="module")
def xsd_schema() -> etree.XMLSchema:
    root = etree.parse(str(TOOL_XSD_FILE))
    schema = etree.XMLSchema(root)
    return schema


class TestGalaxyToolValidationServiceClass:
    def test_validate_document_returns_empty_diagnostics_when_valid(self, xsd_schema: etree.XMLSchema) -> None:
        service = GalaxyToolValidationService(TEST_SERVER_NAME, xsd_schema)
        xml_document = TestUtils.from_document_to_xml_document(TEST_TOOL_01_DOCUMENT)

        actual = service.validate_document(xml_document)

        assert actual == []

    def test_validate_macro_file_returns_empty_diagnostics_when_valid(self, xsd_schema: etree.XMLSchema) -> None:
        service = GalaxyToolValidationService(TEST_SERVER_NAME, xsd_schema)
        xml_document = TestUtils.from_document_to_xml_document(TEST_MACRO_01_DOCUMENT)

        actual = service.validate_document(xml_document)

        assert actual == []

    def test_validate_document_returns_diagnostics_when_invalid(self, xsd_schema: etree.XMLSchema) -> None:
        service = GalaxyToolValidationService(TEST_SERVER_NAME, xsd_schema)
        xml_document = TestUtils.from_document_to_xml_document(TEST_INVALID_TOOL_01_DOCUMENT)

        actual = service.validate_document(xml_document)

        assert len(actual) > 0

    def test_validate_document_returns_diagnostics_when_syntax_error(self, xsd_schema: etree.XMLSchema) -> None:
        service = GalaxyToolValidationService(TEST_SERVER_NAME, xsd_schema)
        xml_document = TestUtils.from_document_to_xml_document(TEST_SYNTAX_ERROR_TOOL_01_DOCUMENT)

        actual = service.validate_document(xml_document)

        assert len(actual) == 1

    def test_validate_macro_file_returns_diagnostics_when_syntax_error(self, xsd_schema: etree.XMLSchema) -> None:
        service = GalaxyToolValidationService(TEST_SERVER_NAME, xsd_schema)
        xml_document = TestUtils.from_document_to_xml_document(TEST_SYNTAX_ERROR_MACRO_01_DOCUMENT)

        actual = service.validate_document(xml_document)

        assert len(actual) == 1
