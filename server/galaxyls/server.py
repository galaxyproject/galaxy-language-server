"""Galaxy Tools Language Server implementation"""

from typing import List, Optional

from lsprotocol.types import (
    INITIALIZED,
    TEXT_DOCUMENT_CODE_ACTION,
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DEFINITION,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE,
    TEXT_DOCUMENT_DOCUMENT_LINK,
    TEXT_DOCUMENT_DOCUMENT_SYMBOL,
    TEXT_DOCUMENT_FORMATTING,
    TEXT_DOCUMENT_HOVER,
    WORKSPACE_DID_CHANGE_CONFIGURATION,
    CodeAction,
    CodeActionKind,
    CodeActionOptions,
    CodeActionParams,
    CompletionList,
    CompletionOptions,
    CompletionParams,
    ConfigurationItem,
    Diagnostic,
    DidChangeConfigurationParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
    DocumentFormattingParams,
    DocumentLink,
    DocumentLinkParams,
    DocumentSymbol,
    DocumentSymbolParams,
    Hover,
    InitializeParams,
    Location,
    MessageType,
    TextDocumentIdentifier,
    TextDocumentPositionParams,
    TextEdit,
    WorkspaceConfigurationParams,
)
from pygls.server import LanguageServer
from pygls.workspace import Document

from galaxyls.config import CompletionMode, GalaxyToolsConfiguration
from galaxyls.constants import Commands
from galaxyls.services.language import GalaxyToolLanguageService
from galaxyls.services.validation import DocumentValidator
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.parser import XmlDocumentParser
from galaxyls.types import (
    AutoCloseTagResult,
    CommandParameters,
    GeneratedExpandedDocument,
    GeneratedSnippetResult,
    ParamReferencesResult,
    ReplaceTextRangeResult,
    TestSuiteInfoResult,
)
from galaxyls.utils import convert_to
from galaxyls.version import GLS_VERSION

GLS_NAME = "galaxy-tools-language-server"


class GalaxyToolsLanguageServer(LanguageServer):
    """Galaxy Tools Language Server."""

    def __init__(self) -> None:
        super().__init__(name=GLS_NAME, version=GLS_VERSION)
        self.service = GalaxyToolLanguageService()
        self.configuration: GalaxyToolsConfiguration = GalaxyToolsConfiguration()


language_server = GalaxyToolsLanguageServer()


async def _load_client_config_async(server: GalaxyToolsLanguageServer) -> None:
    """Loads the client configuration from user or workspace settings and updates
    the language server configuration.

    Args:
        server (GalaxyToolsLanguageServer): The language server instance.
    """
    try:
        config = await server.get_configuration_async(
            WorkspaceConfigurationParams(items=[ConfigurationItem(section="galaxyTools")])
        )
        server.configuration = convert_to(config[0], GalaxyToolsConfiguration)
    except BaseException as err:
        server.show_message_log(f"Error loading configuration: {err}")
        server.show_message("Error loading configuration. Using default settings.", MessageType.Error)


@language_server.feature(INITIALIZED)
async def initialized(server: GalaxyToolsLanguageServer, params: InitializeParams) -> None:
    """Loads the client configuration after initialization."""
    await _load_client_config_async(server)
    server.service.set_workspace(server.workspace)


@language_server.feature(WORKSPACE_DID_CHANGE_CONFIGURATION)
async def did_change_configuration(server: GalaxyToolsLanguageServer, params: DidChangeConfigurationParams) -> None:
    """Loads the client configuration after a change."""
    await _load_client_config_async(server)
    server.show_message("Settings updated")


@language_server.feature(TEXT_DOCUMENT_COMPLETION, CompletionOptions(trigger_characters=["<", " "]))
def completions(server: GalaxyToolsLanguageServer, params: CompletionParams) -> Optional[CompletionList]:
    """Returns completion items depending on the current document context."""
    if server.configuration.completion.mode == CompletionMode.DISABLED:
        return None
    document = _get_valid_document(server, params.text_document.uri)
    if document:
        xml_document = _get_xml_document(document)
        return server.service.get_completion(xml_document, params, server.configuration.completion.mode)
    return None


@language_server.feature(TEXT_DOCUMENT_HOVER)
def hover(server: GalaxyToolsLanguageServer, params: TextDocumentPositionParams) -> Optional[Hover]:
    """Displays Markdown documentation for the element under the cursor."""
    document = _get_valid_document(server, params.text_document.uri)
    if document:
        xml_document = _get_xml_document(document)
        return server.service.get_documentation(xml_document, params.position)
    return None


@language_server.feature(TEXT_DOCUMENT_FORMATTING)
def formatting(server: GalaxyToolsLanguageServer, params: DocumentFormattingParams) -> Optional[List[TextEdit]]:
    """Formats the whole document using the provided parameters"""
    document = _get_valid_document(server, params.text_document.uri)
    if document:
        content = document.source
        return server.service.format_document(content, params)
    return None


@language_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(server: GalaxyToolsLanguageServer, params: DidOpenTextDocumentParams) -> None:
    """Occurs when a new xml document is open."""
    document = server.workspace.get_document(params.text_document.uri)
    if not DocumentValidator.is_empty_document(document):
        _validate(server, params)


@language_server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(server: GalaxyToolsLanguageServer, params: DidSaveTextDocumentParams) -> None:
    """Occurs when the xml document is saved to disk."""
    _validate(server, params)


@language_server.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(server: GalaxyToolsLanguageServer, params: DidCloseTextDocumentParams) -> None:
    """Occurs when the xml document is closed."""
    server.publish_diagnostics(params.text_document.uri, [])


@language_server.feature(TEXT_DOCUMENT_DEFINITION)
def definition(server: GalaxyToolsLanguageServer, params: TextDocumentPositionParams) -> Optional[List[Location]]:
    """Provides the location of a symbol definition."""
    document = _get_valid_document(server, params.text_document.uri)
    if document:
        xml_document = _get_xml_document(document)
        return server.service.go_to_definition(xml_document, params.position)
    return None


@language_server.feature(TEXT_DOCUMENT_DOCUMENT_LINK)
def document_link(server: GalaxyToolsLanguageServer, params: DocumentLinkParams) -> List[DocumentLink]:
    document = _get_valid_document(server, params.text_document.uri)
    if document:
        xml_document = _get_xml_document(document)
        return server.service.link_provider.get_document_links(xml_document)
    return []


@language_server.feature(
    TEXT_DOCUMENT_CODE_ACTION,
    CodeActionOptions(
        code_action_kinds=[
            CodeActionKind.RefactorExtract,
        ],
    ),
)
def process_code_actions(server: GalaxyToolsLanguageServer, params: CodeActionParams) -> Optional[List[CodeAction]]:
    document = _get_valid_document(server, params.text_document.uri)
    if document is None:
        return None
    xml_document = _get_xml_document(document)
    return server.service.get_available_refactoring_actions(xml_document, params)


@language_server.feature(TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(server: GalaxyToolsLanguageServer, params: DocumentSymbolParams) -> Optional[List[DocumentSymbol]]:
    """Returns a list of symbols defined in the document."""
    document = _get_valid_document(server, params.text_document.uri)
    if document:
        xml_document = _get_xml_document(document)
        return server.service.symbols_provider.get_document_symbols(xml_document)
    return None


@language_server.command(Commands.AUTO_CLOSE_TAGS)
def auto_close_tag(server: GalaxyToolsLanguageServer, parameters: CommandParameters) -> Optional[AutoCloseTagResult]:
    """Responds to a close tag request to close the currently opened node."""
    if server.configuration.completion.auto_close_tags and parameters:
        params = convert_to(parameters[0], TextDocumentPositionParams)
        document = _get_valid_document(server, params.text_document.uri)
        if document:
            xml_document = _get_xml_document(document)
            return server.service.get_auto_close_tag(xml_document, params.position)
    return None


@language_server.command(Commands.GENERATE_TESTS)
async def cmd_generate_test(
    server: GalaxyToolsLanguageServer, parameters: CommandParameters
) -> Optional[GeneratedSnippetResult]:
    """Generates some test snippets based on the inputs and outputs of the document."""
    params = convert_to(parameters[0], TextDocumentIdentifier)
    document = _get_valid_document(server, params.uri)
    if document:
        return server.service.generate_tests(document)
    return None


@language_server.command(Commands.GENERATE_COMMAND)
async def cmd_generate_command(
    server: GalaxyToolsLanguageServer, parameters: CommandParameters
) -> Optional[GeneratedSnippetResult]:
    """Generates a boilerplate Cheetah code snippet based on the inputs and outputs of the document."""
    params = convert_to(parameters[0], TextDocumentIdentifier)
    document = _get_valid_document(server, params.uri)
    if document:
        return server.service.generate_command(document)
    return None


@language_server.command(Commands.SORT_SINGLE_PARAM_ATTRS)
def sort_single_param_attrs_command(
    server: GalaxyToolsLanguageServer, parameters: CommandParameters
) -> Optional[ReplaceTextRangeResult]:
    """Sorts the attributes of the param element under the cursor."""
    params = convert_to(parameters[0], TextDocumentPositionParams)
    document = _get_valid_document(server, params.text_document.uri)
    if document:
        xml_document = _get_xml_document(document)
        return server.service.sort_single_param_attrs(xml_document, params.position)
    return None


@language_server.command(Commands.SORT_DOCUMENT_PARAMS_ATTRS)
def sort_document_params_attrs_command(
    server: GalaxyToolsLanguageServer, parameters: CommandParameters
) -> Optional[List[ReplaceTextRangeResult]]:
    """Sorts the attributes of all the param elements contained in the document."""
    params = convert_to(parameters[0], TextDocumentIdentifier)
    document = _get_valid_document(server, params.uri)
    if document:
        xml_document = _get_xml_document(document)
        return server.service.sort_document_param_attributes(xml_document)
    return None


@language_server.command(Commands.GENERATE_EXPANDED_DOCUMENT)
def generate_expanded_command(server: GalaxyToolsLanguageServer, parameters: CommandParameters) -> GeneratedExpandedDocument:
    """Generates a expanded version (with all macros replaced) of the tool document."""
    params = convert_to(parameters[0], TextDocumentIdentifier)
    document = server.workspace.get_document(params.uri)
    if document and DocumentValidator.is_tool_document(document):
        return server.service.macro_expander.generate_expanded_from(document.path)
    return GeneratedExpandedDocument(errorMessage=f"The document {document.filename} is not a valid Galaxy Tool wrapper.")


@language_server.command(Commands.DISCOVER_TESTS_IN_WORKSPACE)
def discover_tests_in_workspace_command(
    server: GalaxyToolsLanguageServer, parameters: CommandParameters
) -> List[TestSuiteInfoResult]:
    """Returns a list of test suites, one for each tool file in the workspace."""
    return server.service.test_discovery_service.discover_tests_in_workspace(server.workspace)


@language_server.command(Commands.DISCOVER_TESTS_IN_DOCUMENT)
def discover_tests_in_document_command(
    server: GalaxyToolsLanguageServer, parameters: CommandParameters
) -> Optional[TestSuiteInfoResult]:
    """Returns a test suite containing all tests for a particular XML tool document."""
    params = convert_to(parameters[0], TextDocumentIdentifier)
    document = _get_valid_document(server, params.uri)
    if document:
        xml_document = _get_xml_document(document)
        return server.service.test_discovery_service.discover_tests_in_document(xml_document)
    return None


@language_server.command(Commands.INSERT_PARAM_REFERENCE)
async def cmd_insert_param_reference(
    server: GalaxyToolsLanguageServer, parameters: CommandParameters
) -> Optional[ParamReferencesResult]:
    """Provides a list of possible parameter references to be inserted in the command section of the document."""
    params = convert_to(parameters[0], TextDocumentIdentifier)
    document = _get_valid_document(server, params.uri)
    if document:
        xml_document = _get_xml_document(document)
        return server.service.param_references_provider.get_param_command_references(xml_document)
    return None


@language_server.command(Commands.INSERT_PARAM_FILTER_REFERENCE)
async def cmd_insert_param_filter_reference(
    server: GalaxyToolsLanguageServer, parameters: CommandParameters
) -> Optional[ParamReferencesResult]:
    """Provides a list of possible parameter references to be inserted as output filters."""
    params = convert_to(parameters[0], TextDocumentIdentifier)
    document = _get_valid_document(server, params.uri)
    if document:
        xml_document = _get_xml_document(document)
        return server.service.param_references_provider.get_param_filter_references(xml_document)
    return None


def _validate(server: GalaxyToolsLanguageServer, params) -> None:
    """Validates the Galaxy tool and reports any problem found."""
    diagnostics: List[Diagnostic] = []
    document = _get_valid_document(server, params.text_document.uri)
    if document:
        xml_document = _get_xml_document(document)
        diagnostics = server.service.get_diagnostics(xml_document)
    server.publish_diagnostics(params.text_document.uri, diagnostics)


def _get_valid_document(server: GalaxyToolsLanguageServer, uri: str) -> Optional[Document]:
    document = server.workspace.get_document(uri)
    if _is_document_supported(document):
        return document
    return None


def _get_xml_document(document: Document) -> XmlDocument:
    """Parses the input Document and returns an XmlDocument."""
    xml_document = XmlDocumentParser().parse(document)
    return xml_document


def _is_document_supported(document: Document) -> bool:
    """Returns True if the given document is supported by the server."""
    if not document.uri.lower().endswith(".xml"):
        return False
    return DocumentValidator.has_valid_root(document)
