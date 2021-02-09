from typing import List, Optional

from galaxyls.services.tools.common import TestsDiscoveryService, ToolParamAttributeSorter
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.tools.generators.command import GalaxyToolCommandSnippetGenerator
from galaxyls.services.tools.generators.tests import GalaxyToolTestSnippetGenerator
from galaxyls.services.tools.iuc import IUCToolParamAttributeSorter
from pygls.types import (
    CompletionList,
    CompletionParams,
    Diagnostic,
    DocumentFormattingParams,
    Hover,
    Position,
    TextDocumentPositionParams,
    TextEdit,
)
from pygls.workspace import Document, Workspace

from galaxyls.services.tools.testing import ToolTestsDiscoveryService

from ..config import CompletionMode
from ..types import GeneratedSnippetResult, ReplaceTextRangeResult, TestSuiteInfoResult
from .completion import AutoCloseTagResult, XmlCompletionService
from .context import XmlContextService
from .format import GalaxyToolFormatService
from .xml.document import XmlDocument
from .xsd.service import GalaxyToolXsdService


class GalaxyToolLanguageService:
    """Galaxy tool Language service.

    This service manages all the operations supported
    by the LSP.
    """

    def __init__(self, server_name: str):
        self.xsd_service = GalaxyToolXsdService(server_name)
        self.format_service = GalaxyToolFormatService()
        tree = self.xsd_service.xsd_parser.get_tree()
        self.completion_service = XmlCompletionService(tree)
        self.xml_context_service = XmlContextService(tree)
        self.sort_service: ToolParamAttributeSorter = IUCToolParamAttributeSorter()
        self.test_discovery_service: TestsDiscoveryService = ToolTestsDiscoveryService()

    def get_diagnostics(self, xml_document: XmlDocument) -> List[Diagnostic]:
        """Validates the Galaxy tool XML document and returns a list
        of diagnotics if there are any problems.
        """
        return self.xsd_service.validate_document(xml_document)

    def get_documentation(self, xml_document: XmlDocument, position: Position) -> Optional[Hover]:
        """Gets the documentation about the element at the given position."""
        context = self.xml_context_service.get_xml_context(xml_document, position)
        if context.token and (context.is_tag or context.is_attribute_key):
            documentation = self.xsd_service.get_documentation_for(context)
            context_range = self.xml_context_service.get_range_for_context(xml_document, context)
            return Hover(documentation, context_range)
        return None

    def format_document(self, content: str, params: DocumentFormattingParams) -> List[TextEdit]:
        """Given the document contents returns the list of TextEdits
        needed to properly format and layout the document.
        """
        return self.format_service.format(content, params)

    def get_completion(
        self, xml_document: XmlDocument, params: CompletionParams, mode: CompletionMode
    ) -> Optional[CompletionList]:
        """Gets completion items depending on the current document context."""
        context = self.xml_context_service.get_xml_context(xml_document, params.position)
        return self.completion_service.get_completion_at_context(context, params.context, mode)

    def get_auto_close_tag(
        self, xml_document: XmlDocument, params: TextDocumentPositionParams
    ) -> Optional[AutoCloseTagResult]:
        """Gets the closing result for the currently opened tag in context."""
        trigger_character = xml_document.document.lines[params.position.line][params.position.character - 1]
        position_before_trigger = Position(params.position.line, params.position.character - 1)
        context = self.xml_context_service.get_xml_context(xml_document, position_before_trigger)
        return self.completion_service.get_auto_close_tag(context, trigger_character)

    def generate_tests(self, document: Document) -> Optional[GeneratedSnippetResult]:
        """Generates a code snippet with some tests for the current inputs and outputs
        of this tool wrapper."""
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolTestSnippetGenerator(tool)
        return generator.generate_snippet()

    def generate_command(self, document: Document) -> Optional[GeneratedSnippetResult]:
        """Generates a boilerplate Cheetah code snippet based on the current inputs and outputs
        of this tool wrapper."""
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolCommandSnippetGenerator(tool)
        return generator.generate_snippet()

    def sort_single_param_attrs(
        self, xml_document: XmlDocument, params: TextDocumentPositionParams
    ) -> Optional[ReplaceTextRangeResult]:
        """Sorts the attributes of the param element under the cursor."""
        offset = xml_document.document.offset_at_position(params.position)
        param_element = xml_document.find_element_at(offset)
        if param_element:
            return self.sort_service.sort_param_attributes(param_element, xml_document)
        return None

    def sort_document_param_attributes(self, xml_document: XmlDocument) -> List[ReplaceTextRangeResult]:
        """Sorts the attributes of all the param elements contained in the document."""
        return self.sort_service.sort_document_param_attributes(xml_document)

    def discover_tests(self, workspace: Workspace) -> List[TestSuiteInfoResult]:
        """Sorts the attributes of all the param elements contained in the document."""
        return self.test_discovery_service.discover_tests_in_workspace(workspace)
