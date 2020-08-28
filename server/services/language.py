from .xsd.service import GalaxyToolXsdService
from .format import GalaxyToolFormatService
from .completion import CompletionService
from .context import XmlContextService
from ..utils.pygls_utils import get_word_at_position

from typing import List
from pygls.workspace import Document
from pygls.types import (
    CompletionList,
    CompletionParams,
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
        self.completion_service = CompletionService(tree)
        self.xml_context_service = XmlContextService(tree)

    def get_diagnostics(self, content: str) -> List[Diagnostic]:
        """Validates the Galaxy tool and returns a list
        of diagnotics if there are any problems.
        """
        return self.xsd_service.validate_xml(content)

    def get_documentation(self, document: Document, position: Position) -> str:
        """Gets the documentation about the element at the given position."""

        # TODO: use context to get a real *keyword* (tag, attribute)
        word = get_word_at_position(document, position)

        if not word:
            return None

        documentation = self.xsd_service.get_documentation_for(word.text)

        return Hover(documentation, word.range)

    def format_document(
        self, content: str, params: DocumentFormattingParams
    ) -> List[TextEdit]:
        """Given the document contents returns the list of TextEdits
        needed to properly format and layout the document.
        """
        return self.format_service.format(content, params)

    def get_completion(
        self, document: Document, params: CompletionParams
    ) -> CompletionList:
        """Gets completion items depending on the current document context."""
        xml_content = document.source
        offset = document.offset_at_position(params.position)

        offset = offset - 1  # ignore completion trigger
        context = self.xml_context_service.get_xml_context(xml_content, offset)

        if params.context.triggerCharacter == "<":
            return self.completion_service.get_node_completion(context)
        if params.context.triggerCharacter == " ":
            return self.completion_service.get_attribute_completion(context)
