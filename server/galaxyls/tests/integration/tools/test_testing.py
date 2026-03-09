from typing import (
    cast,
)

import pytest
from pygls.workspace import (
    TextDocument,
    Workspace,
)
from pytest_mock import MockerFixture

from galaxyls.services.tools.testing import ToolTestsDiscoveryService
from galaxyls.tests.unit.utils import TestUtils

TEST_DOCUMENTS = [
    "tool_with_tests_01.xml",
    "tool_with_tests_02.xml",
]


def get_document_by_name(name: str) -> TextDocument | None:
    if name in TEST_DOCUMENTS:
        return TestUtils.get_test_document_from_file(name)
    return None


@pytest.fixture()
def fake_workspace(mocker: MockerFixture) -> Workspace:
    workspace_documents: dict[str, TextDocument] = {}
    for doc_name in TEST_DOCUMENTS:
        doc = get_document_by_name(doc_name)
        if doc:
            workspace_documents[doc.uri] = doc

    def get_text_document(uri: str) -> TextDocument:
        return workspace_documents[uri]

    workspace = mocker.Mock()
    workspace.text_documents = workspace_documents.keys()
    workspace.get_text_document.side_effect = get_text_document
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
