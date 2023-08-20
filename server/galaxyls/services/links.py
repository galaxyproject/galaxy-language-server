from typing import List

from lsprotocol.types import DocumentLink

from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.utils import convert_document_offsets_to_range


class DocumentLinksProvider:
    """Provides links to external resources defined in the document."""

    def get_document_links(self, xml_document: XmlDocument) -> List[DocumentLink]:
        tool = GalaxyToolXmlDocument.from_xml_document(xml_document)
        test_data_file_links = self._get_test_data_file_links(tool)
        return test_data_file_links

    def _get_test_data_file_links(self, tool: GalaxyToolXmlDocument) -> List[DocumentLink]:
        result: List[DocumentLink] = []
        for test in tool.get_tests():
            params = filter(lambda e: e.name == "param", test.elements)
            for param in params:
                value_attr = param.attributes.get("value")
                if value_attr is None or value_attr.value is None:
                    # Must have a value
                    continue

                filename = value_attr.get_value()
                if filename is None or "." not in filename:
                    # Must be a filename with extension
                    continue

                test_data_file_path = tool.get_test_data_path() / filename
                start_offset, end_offset = value_attr.value.get_unquoted_content_offsets()
                link_range = convert_document_offsets_to_range(tool.xml_document.document, start_offset, end_offset)
                result.append(
                    DocumentLink(
                        target=test_data_file_path.as_uri(),
                        range=link_range,
                    )
                )
        return result
