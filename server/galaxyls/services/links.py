from typing import List

from lsprotocol.types import DocumentLink

from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.nodes import XmlElement
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
                value_attribute = param.attributes.get("value")
                filename = param.get_attribute_value("value")
                if not value_attribute or not value_attribute.value or not filename:
                    # Must have a value
                    continue

                if not self._is_data_input_param(param, tool):
                    continue

                test_data_file_path = tool.get_test_data_path() / filename
                start_offset, end_offset = value_attribute.value.get_unquoted_content_offsets()
                link_range = convert_document_offsets_to_range(tool.xml_document.document, start_offset, end_offset)
                result.append(
                    DocumentLink(
                        target=test_data_file_path.as_uri(),
                        range=link_range,
                    )
                )
        return result

    def _is_data_input_param(self, param: XmlElement, tool: GalaxyToolXmlDocument) -> bool:
        param_name = param.get_attribute_value("name")
        inputs = tool.get_inputs()
        for input in inputs:
            input_name = input.get_attribute_value("name")
            if input_name == param_name:
                input_type = input.get_attribute_value("type")
                return input_type == "data"
        return False
