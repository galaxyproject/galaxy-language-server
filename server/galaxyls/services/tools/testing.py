from typing import List, Optional

from pygls.workspace import Document, Workspace
from galaxyls.services.tools.common import TestsDiscoveryService
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.xml.parser import XmlDocumentParser
from galaxyls.services.xml.utils import convert_document_offset_to_line
from galaxyls.types import TestInfoResult, TestSuiteInfoResult
from galaxyls.services.validation import DocumentValidator


class ToolTestsDiscoveryService(TestsDiscoveryService):
    document_validator = DocumentValidator()

    def discover_tests_in_workspace(self, workspace: Workspace) -> List[TestSuiteInfoResult]:
        rval: List[TestSuiteInfoResult] = []
        for doc_uri in workspace.documents:
            document = workspace.get_document(doc_uri)
            if self.document_validator.is_tool_document(document):
                test_suite = self._get_test_suite_from_document(document)
                if test_suite:
                    rval.append(test_suite)
        return rval

    def _get_test_suite_from_document(self, document: Document) -> Optional[TestSuiteInfoResult]:
        xml_document = XmlDocumentParser().parse(document)
        tool = GalaxyToolXmlDocument.from_xml_document(xml_document)
        tool_id = tool.get_tool_id()
        if tool_id:
            tests = tool.get_tests()
            suite_tests: List[TestInfoResult] = []
            id = 1
            for test in tests:
                line = convert_document_offset_to_line(xml_document.document, test.start_tag_open_offset)
                suite_tests.append(
                    TestInfoResult(
                        tool_id=tool_id,
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
