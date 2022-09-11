import abc
from typing import (
    List,
    Optional,
)

from pygls.lsp.types import Diagnostic
from pygls.workspace import Workspace

from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.nodes import XmlElement
from galaxyls.types import (
    ReplaceTextRangeResult,
    TestSuiteInfoResult,
)


class ToolParamAttributeSorter(metaclass=abc.ABCMeta):
    """Interface to sort attributes inside an element and return them as a document replace range edit.

    The sort criteria is defined by the implementing class.
    """

    @abc.abstractmethod
    def sort_param_attributes(self, param: XmlElement, xml_document: XmlDocument) -> Optional[ReplaceTextRangeResult]:
        """Returns a document replace edit with the sorted attributes of the given param contained in the xml_document."""
        raise NotImplementedError

    @abc.abstractmethod
    def sort_document_param_attributes(self, xml_document: XmlDocument) -> List[ReplaceTextRangeResult]:
        """Returns a collection of edits with all the attributes of the param elements in the document sorted."""
        raise NotImplementedError


class TestsDiscoveryService(metaclass=abc.ABCMeta):
    """Interface class for test discovering."""

    @abc.abstractmethod
    def discover_tests_in_workspace(self, workspace: Workspace) -> List[TestSuiteInfoResult]:
        raise NotImplementedError

    @abc.abstractmethod
    def discover_tests_in_document(self, xml_document: XmlDocument) -> Optional[TestSuiteInfoResult]:
        raise NotImplementedError


class ToolLinter(metaclass=abc.ABCMeta):
    """Interface class for linting tool documents."""

    @abc.abstractmethod
    def lint_document(self, xml_document: XmlDocument) -> List[Diagnostic]:
        """Returns a list of diagnostics with all the issues found in the given document."""
        raise NotImplementedError
