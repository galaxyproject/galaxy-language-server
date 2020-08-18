"""Galaxy xml tools Language Server implementation"""

import asyncio
import uuid
import os

from lxml import etree

from pygls.server import LanguageServer
from pygls.features import (TEXT_DOCUMENT_DID_OPEN,
                            TEXT_DOCUMENT_DID_CHANGE,
                            TEXT_DOCUMENT_DID_SAVE,
                            TEXT_DOCUMENT_DID_CLOSE)
from pygls.types import (CompletionItem, CompletionList, CompletionParams,
                         ConfigurationItem, ConfigurationParams, Diagnostic,
                         DidOpenTextDocumentParams,
                         DidChangeTextDocumentParams,
                         DidSaveTextDocumentParams,
                         DidCloseTextDocumentParams,
                         MessageType, Position, Range, Registration,
                         RegistrationParams, Unregistration,
                         UnregistrationParams)


TOOL_XSD = os.path.join(os.path.dirname(__file__), 'xsd', "galaxy.xsd")


class GalaxyToolsLanguageServer(LanguageServer):

    xsd_doc = etree.parse(TOOL_XSD)

    def __init__(self):
        super().__init__()


language_server = GalaxyToolsLanguageServer()


@language_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Xml document did open notification."""
    ls.show_message('Xml Document Open')
    _validate(ls, params)


@language_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls, params: DidChangeTextDocumentParams):
    """Xml document did change notification."""
    _validate(ls, params)


@language_server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls, params: DidSaveTextDocumentParams):
    """Xml document did save notification."""
    ls.show_message('Xml Document Saved')


@language_server.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(server: GalaxyToolsLanguageServer, params: DidCloseTextDocumentParams):
    """Xml document did close notification."""
    server.show_message('Xml Document Closed')


def _validate(ls, params):
    """Validates the Galaxy tool"""
    text_doc = ls.workspace.get_document(params.textDocument.uri)

    diagnostics = _validate_xml(text_doc.source)
    ls.publish_diagnostics(text_doc.uri, diagnostics)


def _validate_xml(source):
    """Validates the Galaxy tool xml using the XSD schema."""
    diagnostics = []
    try:
        xsd = etree.XMLSchema(GalaxyToolsLanguageServer.xsd_doc)
        xml = etree.fromstring(source)
        xsd.assertValid(xml)
    except etree.DocumentInvalid as e:
        diagnostics = _build_diagnostics(e.error_log)
    except etree.XMLSyntaxError as e:
        diagnostics = build_diagnostics_from_XMLSyntaxError(e)

    return diagnostics


def _build_diagnostics(error_log):
    """Gets a list of Diagnostic elements resulting from the xml validation."""
    diagnostics = []
    for error in error_log.filter_from_errors():
        result = Diagnostic(
            Range(
                Position(error.line - 1, error.column),
                Position(error.line - 1, error.column)
            ),
            error.message,
            source=type(language_server).__name__
        )
        diagnostics.append(result)

    return diagnostics


def build_diagnostics_from_XMLSyntaxError(e: etree.XMLSyntaxError):
    """Builds a Diagnostic element from the XMLSyntaxError."""
    result = Diagnostic(
        Range(
            Position(e.lineno - 1, e.position[0]-1),
            Position(e.lineno - 1, e.position[1]-1)
        ),
        e.msg,
        source=type(language_server).__name__
    )

    return [result]
