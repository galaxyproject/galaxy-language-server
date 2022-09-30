import pytest
from lxml import etree

from galaxyls.services.validation import DocumentValidator
from ...services.xsd.constants import TOOL_XSD_FILE
from .utils import TestUtils


@pytest.fixture(scope="module")
def xsd_schema() -> etree.XMLSchema:
    root = etree.parse(str(TOOL_XSD_FILE))
    schema = etree.XMLSchema(root)
    return schema


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
