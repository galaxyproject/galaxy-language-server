
from .xsd import GalaxyToolXsdService
from ..utils.pygls_utils import get_word_at_position

from typing import List
from pygls.workspace import Document
from pygls.types import (
    Diagnostic,
    Hover,
    MarkupContent,
    MarkupKind,
    Position,
    Range
)


class GalaxyToolLanguageService():
    """Galaxy tool Language service.

    This service manages all the operations supported
    by the LSP.
    """

    def __init__(self, server_name: str):
        self.xsd_service = GalaxyToolXsdService(server_name)

    def get_diagnostics(self, source: str) -> List[Diagnostic]:
        """Validates the Galaxy tool and returns a list
        of diagnotics if there are any problems.
        """
        return self.xsd_service.validate_xml(source)

    def get_documentation(self, document: Document, position: Position) -> str:
        """Gets the documentation about the element at the given position."""
        word = get_word_at_position(document, position)

        if not word:
            return None

        documentation = self.xsd_service.get_documentation_for(word.text)

        return Hover(MarkupContent(MarkupKind.Markdown, documentation), word.position_range)
