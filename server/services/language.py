
from .xsd import GalaxyToolXsdService
from .format import GalaxyToolFormatService
from ..utils.pygls_utils import get_word_at_position

from typing import List
from pygls.workspace import Document
from pygls.types import (
    Diagnostic,
    DocumentFormattingParams,
    Hover,
    MarkupContent,
    MarkupKind,
    Position,
    Range,
    TextEdit
)


class GalaxyToolLanguageService():
    """Galaxy tool Language service.

    This service manages all the operations supported
    by the LSP.
    """

    def __init__(self, server_name: str):
        self.xsd_service = GalaxyToolXsdService(server_name)
        self.format_service = GalaxyToolFormatService()

    def get_diagnostics(self, content: str) -> List[Diagnostic]:
        """Validates the Galaxy tool and returns a list
        of diagnotics if there are any problems.
        """
        return self.xsd_service.validate_xml(content)

    def get_documentation(self, document: Document, position: Position) -> str:
        """Gets the documentation about the element at the given position."""
        word = get_word_at_position(document, position)

        if not word:
            return None

        documentation = self.xsd_service.get_documentation_for(word.text)

        return Hover(MarkupContent(MarkupKind.Markdown, documentation), word.position_range)

    def format_document(self, content: str,
                        params: DocumentFormattingParams) -> List[TextEdit]:
        """Given the document contents returns the list of TextEdits
        needed to properly layout the document.
        """
        return self.format_service.format(content, params)
