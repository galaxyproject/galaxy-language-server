from typing import Dict, List, Optional, cast
import pytest
from pytest_mock import MockerFixture

from pygls.workspace import Document, Workspace

from galaxyls.services.tools.testing import ToolTestsDiscoveryService
from galaxyls.tests.unit.utils import TestUtils
from galaxyls.types import TestInfoResult


TEST_DOCUMENTS = [
    "tool_with_tests_01.xml",
    "tool_with_tests_02.xml",
]


def get_document_by_name(name: str) -> Optional[Document]:
    if name in TEST_DOCUMENTS:
        return TestUtils.get_test_document_from_file(name)
    return None


@pytest.fixture()
def fake_workspace(mocker: MockerFixture) -> Workspace:
    workspace_documents: Dict[str, Document] = {}
    for doc_name in TEST_DOCUMENTS:
        doc = get_document_by_name(doc_name)
        if doc:
            workspace_documents[doc.uri] = doc

    def get_document(uri: str) -> Document:
        return workspace_documents[uri]

    workspace = mocker.Mock()
    workspace.documents = workspace_documents.keys()
    workspace.get_document.side_effect = get_document
    return cast(Workspace, workspace)


class TestToolTestsDiscoveryServiceClass:
    def test_discover_tests_in_workspace_returns_expected(self, fake_workspace: Workspace) -> None:
        expected_number_of_suites = 2
        expected_number_of_tests_in_suite_01 = 3
        expected_number_of_tests_in_suite_02 = 5
        service = ToolTestsDiscoveryService()

        actual = service.discover_tests_in_workspace(fake_workspace)

        assert len(actual) == expected_number_of_suites
        assert actual[0].children is not None
        assert len(actual[0].children) == expected_number_of_tests_in_suite_01
        assert actual[1].children is not None
        assert len(actual[1].children) == expected_number_of_tests_in_suite_02
