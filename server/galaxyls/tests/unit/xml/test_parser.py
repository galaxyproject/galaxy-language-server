from ....services.xml.types import DocumentType
from ....services.xml.parser import XmlDocumentParser
from ..sample_data import TEST_TOOL_01_DOCUMENT


class TestXmlDocumentParserClass:
    def test_parse(self):
        test_document = TEST_TOOL_01_DOCUMENT
        parser = XmlDocumentParser()

        xml_document = parser.parse(test_document)

        assert xml_document.document_type == DocumentType.TOOL
