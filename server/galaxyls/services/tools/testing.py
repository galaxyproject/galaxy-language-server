from typing import (
    List,
    Optional,
)

from pygls.workspace import Workspace

from galaxyls.services.tools.common import TestsDiscoveryService
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.validation import DocumentValidator
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.parser import XmlDocumentParser
from galaxyls.types import (
    TestInfoResult,
    TestSuiteInfoResult,
)


class ToolTestsDiscoveryService(TestsDiscoveryService):
    document_validator = DocumentValidator()

    def discover_tests_in_workspace(self, workspace: Workspace) -> List[TestSuiteInfoResult]:
        rval: List[TestSuiteInfoResult] = []
        for doc_uri in workspace.documents:
            document = workspace.get_document(doc_uri)
            if self.document_validator.is_tool_document(document):
                xml_document = XmlDocumentParser().parse(document)
                test_suite = self._get_test_suite_from_document(xml_document)
                if test_suite:
                    rval.append(test_suite)
        return rval

    def discover_tests_in_document(self, xml_document: XmlDocument) -> Optional[TestSuiteInfoResult]:
        test_suite = self._get_test_suite_from_document(xml_document)
        return test_suite

    def _get_test_suite_from_document(self, xml_document: XmlDocument) -> Optional[TestSuiteInfoResult]:
        tool = GalaxyToolXmlDocument.from_xml_document(xml_document)
        tool_id = tool.get_tool_id()
        tests_range = tool.get_tests_range()
        if tool_id and tests_range:
            tests = tool.get_tests()
            test_cases: List[TestInfoResult] = []
            id = 1
            for test in tests:
                range = xml_document.get_full_range(test)
                if range:
                    test_cases.append(
                        TestInfoResult(
                            tool_id=tool_id,
                            test_id=str(id),
                            uri=xml_document.document.uri,
                            range=range,
                        ),
                    )
                    id += 1
            return TestSuiteInfoResult(
                tool_id=tool_id,
                uri=xml_document.document.uri,
                range=tests_range,
                children=test_cases,
            )
        return None
