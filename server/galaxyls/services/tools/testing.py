from typing import List, Optional
from galaxyls.services.tools.common import TestsDiscoveryService
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.utils import convert_document_offset_to_line
from galaxyls.types import TestInfoResult, TestSuiteInfoResult


class ToolTestsDiscoveryService(TestsDiscoveryService):
    def discover_tests_in_document(self, xml_document: XmlDocument) -> Optional[TestSuiteInfoResult]:
        tool = GalaxyToolXmlDocument(xml_document.document, xml_document)
        tool_id = tool.get_tool_id()
        if tool_id:
            tests = tool.get_tests()
            suite_tests: List[TestInfoResult] = []
            id = 1
            for test in tests:
                line = convert_document_offset_to_line(xml_document.document, test.start_tag_open_offset)
                suite_tests.append(
                    TestInfoResult(
                        test_id=str(id),
                        file=xml_document.document.path,
                        line=line,
                    ),
                )
                id += 1
            return TestSuiteInfoResult(
                tool_id=tool_id,
                file=xml_document.document.path,
                children=suite_tests,
            )
