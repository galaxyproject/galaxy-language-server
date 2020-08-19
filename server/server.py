"""Galaxy Tools Language Server implementation"""

from .validation import GalaxyToolValidator

from pygls.server import LanguageServer
from pygls.features import (
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_SAVE,
    TEXT_DOCUMENT_DID_CLOSE
)
from pygls.types import (
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
    DidSaveTextDocumentParams,
    DidCloseTextDocumentParams,
    TextDocumentPositionParams,
    Diagnostic,
    Position,
    Range
)

SERVER_NAME = "Galaxy Tools LS"


class GalaxyToolsLanguageServer(LanguageServer):
    """Galaxy Tools Language Server."""

    def __init__(self):
        super().__init__()
        self.validator = GalaxyToolValidator(SERVER_NAME)


language_server = GalaxyToolsLanguageServer()


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
    """Validates the Galaxy tool"""
    text_doc = server.workspace.get_document(params.textDocument.uri)
    diagnostics = server.validator.validate_xml(text_doc.source)
    server.publish_diagnostics(text_doc.uri, diagnostics)
