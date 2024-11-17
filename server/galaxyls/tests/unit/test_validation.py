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
            ("<visualization>", False),
            (
                '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE visualization SYSTEM "../../visualization.dtd">\n<visualization>',
                False,
            ),
            (
                '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE test SYSTEM "../../test.dtd">\n',
                False,
            ),
            (
                '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE test SYSTEM "../../test.dtd">\n<tool',
                True,
            ),
        ],
    )
    def test_has_valid_root_returns_expected(self, source: str, expected: bool) -> None:
        document = TestUtils.to_document(source)
        validator = DocumentValidator()

        actual = validator.has_valid_root(document)

        assert actual == expected

    @pytest.mark.parametrize(
        "source, expected",
        [
            ("", None),
            ("   ", None),
            ("  \n ", None),
            ("test", None),
            ("<", ""),
            ("<tes", "tes"),
            ("<test   ", "test"),
            ("<tool>", "tool"),
            ("  <tool>", "tool"),
            ("\n<tool>", "tool"),
            ("\n  <tool>", "tool"),
            ("  \n  <tool>", "tool"),
            ("unexpected  <tool>", "tool"),
            ("  unexpected  <tool>", "tool"),
            ("\nunexpected\n  <tool>", "tool"),
            ('<?xml version="1.0" encoding="UTF-8"?><tool>', "tool"),
            ('<?xml version="1.0" encoding="UTF-8"?>\n<tool>', "tool"),
            ("<macros>", "macros"),
            ('<?xml version="1.0" encoding="UTF-8"?>\n<macros>', "macros"),
            ("<test>", "test"),
            ('<test attribute="0">', "test"),
            ("<visualization>", "visualization"),
            ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE test SYSTEM "../../test.dtd">\n', None),
            (
                '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE visualization SYSTEM "../../visualization.dtd">\n<visualization>',
                "visualization",
            ),
        ],
    )
    def test_get_document_root_tag_returns_expected(self, source: str, expected: bool) -> None:
        document = TestUtils.to_document(source)
        validator = DocumentValidator()

        actual = validator.get_document_root_tag(document)

        assert actual == expected
