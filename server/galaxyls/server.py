"""Galaxy Tools Language Server implementation
"""

from typing import List, Optional

from pygls.features import (
    COMPLETION,
    FORMATTING,
    HOVER,
    INITIALIZED,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE,
    WORKSPACE_DID_CHANGE_CONFIGURATION,
)
from pygls.server import LanguageServer
from pygls.types import (
    CompletionList,
    CompletionParams,
    ConfigurationItem,
    ConfigurationParams,
    DidChangeConfigurationParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
    DocumentFormattingParams,
    Hover,
    InitializeParams,
    MessageType,
    TextDocumentPositionParams,
    TextEdit,
)

from .config import CompletionMode, GalaxyToolsConfiguration
from .features import AUTO_CLOSE_TAGS
from .services.language import GalaxyToolLanguageService
from .types import AutoCloseTagResult

SERVER_NAME = "Galaxy Tools LS"


class GalaxyToolsLanguageServer(LanguageServer):
    """Galaxy Tools Language Server."""

    def __init__(self):
        super().__init__()
        self.service = GalaxyToolLanguageService(SERVER_NAME)
        self.configuration: GalaxyToolsConfiguration


language_server = GalaxyToolsLanguageServer()


async def _load_client_config_async(server: GalaxyToolsLanguageServer) -> None:
    """Loads the client configuration from user or workspace settings and updates
    the language server configuration.

    Args:
        server (GalaxyToolsLanguageServer): The language server instance.
    """
    try:
        config = await server.get_configuration_async(
            ConfigurationParams([ConfigurationItem(section=GalaxyToolsConfiguration.SECTION)])
        )
        server.configuration = GalaxyToolsConfiguration(config[0])
    except BaseException as err:
        server.configuration = GalaxyToolsConfiguration()
        server.show_message_log(f"Error loading configuration: {err}")
        server.show_message("Error loading configuration. Using default settings.", MessageType.Error)


@language_server.feature(INITIALIZED)
async def initialized(server: GalaxyToolsLanguageServer, params: InitializeParams) -> None:
    """Loads the client configuration after initialization."""
    await _load_client_config_async(server)


@language_server.feature(WORKSPACE_DID_CHANGE_CONFIGURATION)
async def did_change_configuration(server: GalaxyToolsLanguageServer, params: DidChangeConfigurationParams) -> None:
    """Loads the client configuration after a change."""
    await _load_client_config_async(server)
    server.show_message("Settings updated")


@language_server.feature(COMPLETION, trigger_characters=["<", " "])
def completions(server: GalaxyToolsLanguageServer, params: CompletionParams) -> Optional[CompletionList]:
    """Returns completion items depending on the current document context."""
    if server.configuration.completion_mode == CompletionMode.DISABLED:
        return None
    document = server.workspace.get_document(params.textDocument.uri)
    return server.service.get_completion(document, params, server.configuration.completion_mode)


@language_server.feature(AUTO_CLOSE_TAGS)
def auto_close_tag(server: GalaxyToolsLanguageServer, params: TextDocumentPositionParams) -> Optional[AutoCloseTagResult]:
    """Responds to a close tag request to close the currently opened node."""
    if server.configuration.auto_close_tags:
        document = server.workspace.get_document(params.textDocument.uri)
        return server.service.get_auto_close_tag(document, params)


@language_server.feature(HOVER)
def hover(server: GalaxyToolsLanguageServer, params: TextDocumentPositionParams) -> Optional[Hover]:
    """Displays Markdown documentation for the element under the cursor."""
    document = server.workspace.get_document(params.textDocument.uri)
    return server.service.get_documentation(document, params.position)


@language_server.feature(FORMATTING)
def formatting(server: GalaxyToolsLanguageServer, params: DocumentFormattingParams) -> List[TextEdit]:
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
