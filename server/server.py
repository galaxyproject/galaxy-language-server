"""Galaxy Tools Language Server implementation
"""


from .services.language import GalaxyToolLanguageService

from typing import Optional
from pygls.server import LanguageServer
from pygls.features import (
    HOVER,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE
)
from pygls.types import (
    Diagnostic,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
    Hover,
    MarkupContent,
    MarkupKind,
    Position,
    Range,
    TextDocumentPositionParams
)

SERVER_NAME = "Galaxy Tools LS"


class GalaxyToolsLanguageServer(LanguageServer):
    """Galaxy Tools Language Server."""

    def __init__(self):
        super().__init__()
        self.service = GalaxyToolLanguageService(SERVER_NAME)


language_server = GalaxyToolsLanguageServer()


@language_server.feature(HOVER)
def hover(server: GalaxyToolsLanguageServer,
          params: TextDocumentPositionParams) -> Optional[Hover]:
    """Displays Markdown documentation for the element under the cursor."""
    xml_doc = server.workspace.get_document(params.textDocument.uri)
    return server.service.get_documentation(xml_doc, params.position)


@language_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(server: GalaxyToolsLanguageServer, params: DidOpenTextDocumentParams):
    """Occurs when a new xml document is open."""
    server.show_message('Xml Document Opened')
    _validate(server, params)


@language_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(server: GalaxyToolsLanguageServer, params: DidChangeTextDocumentParams):
    """Occurs when the xml document is changed by the user."""
    _validate(server, params)


@language_server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(server: GalaxyToolsLanguageServer, params: DidSaveTextDocumentParams):
    """Occurs when the xml document is saved to disk."""
    _validate(server, params)
    server.show_message('Xml Document Saved')


@language_server.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(server: GalaxyToolsLanguageServer, params: DidCloseTextDocumentParams):
    """Occurs when the xml document is closed."""
    server.show_message('Xml Document Closed')


def _validate(server: GalaxyToolsLanguageServer, params):
    """Validates the Galaxy tool and reports any problem found."""
    xml_doc = server.workspace.get_document(params.textDocument.uri)
    diagnostics = server.service.get_diagnostics(xml_doc.source)
    server.publish_diagnostics(xml_doc.uri, diagnostics)
