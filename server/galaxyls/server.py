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
    TextDocumentIdentifier,
    TextDocumentPositionParams,
    TextEdit,
)
from pygls.workspace import Document

from galaxyls.services.validation import DocumentValidator

from .config import CompletionMode, GalaxyToolsConfiguration
from .features import AUTO_CLOSE_TAGS, CMD_GENERATE_COMMAND, CMD_GENERATE_TEST
from .services.language import GalaxyToolLanguageService
from .services.xml.document import XmlDocument
from .services.xml.parser import XmlDocumentParser
from .types import AutoCloseTagResult, GeneratedSnippetResult

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
    if not _is_document_supported(document):
        return None
    xml_document = _get_xml_document(document)
    return server.service.get_completion(xml_document, params, server.configuration.completion_mode)


@language_server.feature(AUTO_CLOSE_TAGS)
def auto_close_tag(server: GalaxyToolsLanguageServer, params: TextDocumentPositionParams) -> Optional[AutoCloseTagResult]:
    """Responds to a close tag request to close the currently opened node."""
    if server.configuration.auto_close_tags:
        document = server.workspace.get_document(params.textDocument.uri)
        if not _is_document_supported(document):
            return None
        xml_document = _get_xml_document(document)
        return server.service.get_auto_close_tag(xml_document, params)


@language_server.feature(HOVER)
def hover(server: GalaxyToolsLanguageServer, params: TextDocumentPositionParams) -> Optional[Hover]:
    """Displays Markdown documentation for the element under the cursor."""
    document = server.workspace.get_document(params.textDocument.uri)
    if not _is_document_supported(document):
        return None
    xml_document = _get_xml_document(document)
    return server.service.get_documentation(xml_document, params.position)


@language_server.feature(FORMATTING)
def formatting(server: GalaxyToolsLanguageServer, params: DocumentFormattingParams) -> Optional[List[TextEdit]]:
    """Formats the whole document using the provided parameters"""
    document = server.workspace.get_document(params.textDocument.uri)
    if not _is_document_supported(document):
        return None
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


@language_server.feature(CMD_GENERATE_TEST)
async def cmd_generate_test(
    server: GalaxyToolsLanguageServer, params: TextDocumentIdentifier
) -> Optional[GeneratedSnippetResult]:
    """Generates some test snippets based on the inputs and outputs of the document."""
    document = server.workspace.get_document(params.uri)
    return server.service.generate_tests(document)


@language_server.feature(CMD_GENERATE_COMMAND)
async def cmd_generate_command(
    server: GalaxyToolsLanguageServer, params: TextDocumentIdentifier
) -> Optional[GeneratedSnippetResult]:
    """Generates a boilerplate Cheetah code snippet based on the inputs and outputs of the document."""
    document = server.workspace.get_document(params.uri)
    return server.service.generate_command(document)


def _validate(server: GalaxyToolsLanguageServer, params) -> None:
    """Validates the Galaxy tool and reports any problem found."""
    document = server.workspace.get_document(params.textDocument.uri)
    if _is_document_supported(document):
        xml_document = _get_xml_document(document)
        diagnostics = server.service.get_diagnostics(xml_document)
        server.publish_diagnostics(document.uri, diagnostics)


def _get_xml_document(document: Document) -> XmlDocument:
    """Parses the input Document and returns an XmlDocument."""
    xml_document = XmlDocumentParser().parse(document)
    return xml_document


def _is_document_supported(document: Document) -> bool:
    """Returns True if the given document is supported by the server."""
    return DocumentValidator().has_valid_root(document)
