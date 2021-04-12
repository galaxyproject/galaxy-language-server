"""Utilities to validate Galaxy xml tool wrappers.
"""

from pathlib import Path
from typing import List, Optional

from lxml import etree
from pygls.lsp.types import Diagnostic, DiagnosticRelatedInformation, Location, Position, Range
from pygls.workspace import Document

from galaxy.util import xml_macros
from galaxyls.constants import DiagnosticCodes
from galaxyls.services.macros import remove_macros
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.xml.document import XmlDocument

EXPAND_DOCUMENT_URI_SUFFIX = "%20%28Expanded%29"


class GalaxyToolValidationService:
    """Service providing diagnostics for errors in the XML validation."""

    def __init__(self, server_name: str, xsd_schema: etree.XMLSchema):
        """Initializes the validator"""
        self.server_name = server_name
        self.xsd_schema = xsd_schema

    def validate_document(self, xml_document: XmlDocument) -> List[Diagnostic]:
        """Validates the XML document and returns a list of diagnostics
        if there are any problems.

        Args:
            xml_document (XmlDocument): The XML document. Can be a tool wrapper or macro
            definition file.

        Returns:
            List[Diagnostic]: The list of issues found in the document.
        """

        syntax_errors = self._check_syntax(xml_document.document)
        if syntax_errors:
            return syntax_errors

        if not xml_document.is_tool_file:
            return []
        tool = GalaxyToolXmlDocument.from_xml_document(xml_document)
        try:
            xml_tree = etree.fromstring(tool.source)
            return self._validate_tree(xml_tree)
        except ExpandMacrosFoundException:
            result = self._validate_expanded(tool)
            return result
        except etree.XMLSyntaxError as e:
            return self._build_diagnostics_from_syntax_error(e)

    def _check_syntax(self, document: Document) -> List[Diagnostic]:
        """Check if the XML document contains any syntax error and returns it in a list.

        Args:
            document (Document): The XML document.

        Returns:
            List[Diagnostic]: The list containing the syntax error found or an empty list.
        """
        try:
            etree.fromstring(document.source)
            return []
        except etree.XMLSyntaxError as e:
            return self._build_diagnostics_from_syntax_error(e)

    def _validate_expanded(self, tool: GalaxyToolXmlDocument) -> List[Diagnostic]:
        """Validates the document after loading all the macros referenced and expands them.

        Args:
            document (Document): [description]
            xml_tree (etree.ElementTree): [description]

        Returns:
            List[Diagnostic]: [description]
        """
        try:
            expanded_tool_tree, _ = xml_macros.load_with_references(tool.path)
            expanded_xml = remove_macros(expanded_tool_tree)
            root = expanded_xml.getroot()
            self.xsd_schema.assertValid(root)
            return []
        except etree.DocumentInvalid as e:
            diagnostics = self._build_diagnostics_for_expanded_macros(tool, e)
            return diagnostics

        except etree.XMLSyntaxError as e:
            return self._build_diagnostics_for_macros_file_syntax_error(tool, e)

    def _validate_tree(self, xml_tree: etree._ElementTree) -> List[Diagnostic]:
        """Validates an XML tree against the XSD schema.

        Args:
            xml_tree (etree.ElementTree): The root element

        Returns:
            List[Diagnostic]: The diagnosis results
        """
        try:
            self.xsd_schema.assertValid(xml_tree)
            return []
        except etree.DocumentInvalid as e:
            return self._build_diagnostics(e.error_log, xml_tree)

    def _build_diagnostics(
        self, error_log: etree._ListErrorLog, xml_tree: Optional[etree._ElementTree] = None
    ) -> List[Diagnostic]:
        """Gets a list of diagnostics from the XSD validation error log.

        Args:
            error_log (etree._ListErrorLog): The error log generated after XSD schema validation.
            xml_tree (Optional[etree.ElementTree], optional): The element tree associated with
            the error log. Defaults to None.

        Raises:
            ExpandMacrosFoundException: This is raised when a macro ``expand`` element is found in the error log.
            The ``expand`` element is not part of the XSD so, when this exception is raised, we know that
            the document must expand the macros before validation.

        Returns:
            List[Diagnostic]: The list of resulting diagnostic items found in the error log.
        """
        diagnostics = []
        for error in error_log.filter_from_errors():
            if "expand" in error.message:
                raise ExpandMacrosFoundException(xml_tree)

            result = Diagnostic(
                range=Range(
                    start=Position(line=error.line - 1, character=error.column),
                    end=Position(line=error.line - 1, character=error.column),
                ),
                message=error.message,
                source=self.server_name,
            )
            diagnostics.append(result)
        return diagnostics

    def _build_diagnostics_from_syntax_error(self, error: etree.XMLSyntaxError) -> List[Diagnostic]:
        """Builds a Diagnostic element from a XMLSyntaxError.

        Args:
            error (etree.XMLSyntaxError): The syntax error.

        Returns:
            Diagnostic: The converted Diagnostic item.
        """
        result = Diagnostic(
            range=Range(
                start=Position(line=error.lineno - 1, character=error.position[0] - 1),
                end=Position(line=error.lineno - 1, character=error.position[1] - 1),
            ),
            message=error.msg,
            source=self.server_name,
        )
        return [result]

    def _build_diagnostics_for_macros_file_syntax_error(
        self, tool: GalaxyToolXmlDocument, e: etree.XMLSyntaxError
    ) -> List[Diagnostic]:
        result = Diagnostic(
            range=tool.get_import_macro_file_range(e.filename),
            message=e.msg,
            source=self.server_name,
            related_information=[
                DiagnosticRelatedInformation(
                    message="Syntax error found on imported file.",
                    location=Location(
                        uri=Path(e.filename).as_uri(),
                        range=Range(
                            start=Position(line=e.lineno - 1, character=e.offset),
                            end=Position(line=e.lineno - 1, character=e.offset),
                        ),
                    ),
                )
            ],
        )
        return [result]

    def _build_diagnostics_for_expanded_macros(
        self, tool: GalaxyToolXmlDocument, e: etree.DocumentInvalid
    ) -> List[Diagnostic]:
        virtual_uri = tool.xml_document.document.uri.replace("file", "gls-expand")
        diagnostics = [
            Diagnostic(
                range=tool.get_macros_range(),
                message=error.message,
                source=self.server_name,
                code=DiagnosticCodes.INVALID_EXPANDED_TOOL,
                related_information=[
                    DiagnosticRelatedInformation(
                        message=(
                            "The validation error ocurred on the expanded version of "
                            "the document, i.e. after replacing macros. "
                            "Click here to preview the expanded document."
                        ),
                        location=Location(
                            uri=f"{virtual_uri}{EXPAND_DOCUMENT_URI_SUFFIX}",
                            range=Range(
                                start=Position(line=error.line, character=error.column),
                                end=Position(line=error.line, character=error.column),
                            ),
                        ),
                    )
                ],
            )
            for error in e.error_log.filter_from_errors()
        ]
        return diagnostics


class ExpandMacrosFoundException(Exception):
    """This exceptions indicates that the current tool contains
    macros and they should be expanded before validation.
    """
