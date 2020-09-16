from .xsd.service import GalaxyToolXsdService
from .format import GalaxyToolFormatService
from .completion import XmlCompletionService
from .context import XmlContextService

from typing import List, Optional
from pygls.workspace import Document
from pygls.types import (
    CompletionList,
    CompletionParams,
    CompletionTriggerKind,
    Diagnostic,
    DocumentFormattingParams,
    Hover,
    Position,
    TextEdit,
)


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

    def get_diagnostics(self, content: str) -> List[Diagnostic]:
        """Validates the Galaxy tool and returns a list
        of diagnotics if there are any problems.
        """
        return self.xsd_service.validate_xml(content)

    def get_documentation(self, document: Document, position: Position) -> Optional[Hover]:
        """Gets the documentation about the element at the given position."""
        context = self.xml_context_service.get_xml_context(document, position)
        if context.is_node_content:
            return None
        documentation = self.xsd_service.get_documentation_for(context)
        return Hover(documentation, context.token_range)

    def format_document(self, content: str, params: DocumentFormattingParams) -> List[TextEdit]:
        """Given the document contents returns the list of TextEdits
        needed to properly format and layout the document.
        """
        return self.format_service.format(content, params)

    def get_completion(self, document: Document, params: CompletionParams) -> CompletionList:
        """Gets completion items depending on the current document context."""
        triggerKind = params.context.triggerKind
        if triggerKind == CompletionTriggerKind.TriggerCharacter:
            context = self.xml_context_service.get_xml_context(document, params.position)
            if params.context.triggerCharacter == "<":
                return self.completion_service.get_node_completion(context)
            if params.context.triggerCharacter == " ":
                return self.completion_service.get_attribute_completion(context)
