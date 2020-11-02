from ....services.xml.parser import XmlDocumentParser
from ..sample_data import TEST_TOOL_01_DOCUMENT


class TestTolerantXmlParserClass:
    def test_parse(self):
        test_document = TEST_TOOL_01_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert xml_document
