"""Galaxy Tools Language Server implementation
"""

from .services.language import GalaxyToolLanguageService
from .features import AUTO_CLOSE_TAGS
from .types import AutoCloseTagResult
from typing import Optional, List
from pygls.server import LanguageServer
from pygls.features import (
    COMPLETION,
    FORMATTING,
    HOVER,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE,
)
from pygls.types import (
    CompletionList,
    CompletionParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
    DocumentFormattingParams,
    Hover,
    TextDocumentPositionParams,
    TextEdit,
)

SERVER_NAME = "Galaxy Tools LS"


class GalaxyToolsLanguageServer(LanguageServer):
    """Galaxy Tools Language Server."""

    def __init__(self):
        super().__init__()
        self.service = GalaxyToolLanguageService(SERVER_NAME)


language_server = GalaxyToolsLanguageServer()


@language_server.feature(COMPLETION, trigger_characters=["<", " "])
def completions(server: GalaxyToolsLanguageServer, params: CompletionParams) -> CompletionList:
    """Returns completion items depending on the current document context."""
    document = server.workspace.get_document(params.textDocument.uri)
    return server.service.get_completion(document, params)


@language_server.feature(AUTO_CLOSE_TAGS)
def auto_close_tag(
    server: GalaxyToolsLanguageServer, params: TextDocumentPositionParams
) -> AutoCloseTagResult:
    """Responds to a close tag request to close the currently opened node."""
    document = server.workspace.get_document(params.textDocument.uri)
    return server.service.get_auto_close_tag(document, params)


@language_server.feature(HOVER)
def hover(
    server: GalaxyToolsLanguageServer, params: TextDocumentPositionParams
) -> Optional[Hover]:
    """Displays Markdown documentation for the element under the cursor."""
    document = server.workspace.get_document(params.textDocument.uri)
    return server.service.get_documentation(document, params.position)


@language_server.feature(FORMATTING)
def formatting(
    server: GalaxyToolsLanguageServer, params: DocumentFormattingParams
) -> List[TextEdit]:
    """Formats the whole document using the provided parameters"""
    document = server.workspace.get_document(params.textDocument.uri)
    content = document.source
    return server.service.format_document(content, params)


@language_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(server: GalaxyToolsLanguageServer, params: DidOpenTextDocumentParams) -> None:
    """Occurs when a new xml document is open."""
    _validate(server, params)


@language_server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(server: GalaxyToolsLanguageServer, params: DidSaveTextDocumentParams) -> None:
    """Occurs when the xml document is saved to disk."""
    _validate(server, params)


@language_server.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(server: GalaxyToolsLanguageServer, params: DidCloseTextDocumentParams) -> None:
    """Occurs when the xml document is closed."""
    # server.show_message("Xml Document Closed")


def _validate(server: GalaxyToolsLanguageServer, params) -> None:
    """Validates the Galaxy tool and reports any problem found."""
    document = server.workspace.get_document(params.textDocument.uri)
    diagnostics = server.service.get_diagnostics(document)
    server.publish_diagnostics(document.uri, diagnostics)
