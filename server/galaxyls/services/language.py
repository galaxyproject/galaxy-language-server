from typing import List, Optional

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
from pygls.workspace import Document

from ..config import CompletionMode
from .completion import AutoCloseTagResult, XmlCompletionService
from .context import XmlContextService
from .format import GalaxyToolFormatService
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

    def get_diagnostics(self, document: Document) -> List[Diagnostic]:
        """Validates the Galaxy tool and returns a list
        of diagnotics if there are any problems.
        """
        return self.xsd_service.validate_document(document)

    def get_documentation(self, document: Document, position: Position) -> Optional[Hover]:
        """Gets the documentation about the element at the given position."""
        context = self.xml_context_service.get_xml_context(document, position)
        if context.token and (context.is_tag or context.is_attribute_key):
            documentation = self.xsd_service.get_documentation_for(context)
            context_range = self.xml_context_service.get_range_for_context(document, context)
            return Hover(documentation, context_range)
        return None

    def format_document(self, content: str, params: DocumentFormattingParams) -> List[TextEdit]:
        """Given the document contents returns the list of TextEdits
        needed to properly format and layout the document.
        """
        return self.format_service.format(content, params)

    def get_completion(self, document: Document, params: CompletionParams, mode: CompletionMode) -> CompletionList:
        """Gets completion items depending on the current document context."""
        context = self.xml_context_service.get_xml_context(document, params.position)
        return self.completion_service.get_completion_at_context(context, params.context, mode)

    def get_auto_close_tag(self, document: Document, params: TextDocumentPositionParams) -> Optional[AutoCloseTagResult]:
        """Gets the closing result for the currently opened tag in context."""
        trigger_character = document.lines[params.position.line][params.position.character - 1]
        position_before_trigger = Position(params.position.line, params.position.character - 1)
        context = self.xml_context_service.get_xml_context(document, position_before_trigger)
        return self.completion_service.get_auto_close_tag(context, trigger_character)
