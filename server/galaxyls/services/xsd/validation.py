"""Utilities to validate Galaxy xml tool wrappers.
"""

from pathlib import Path
from typing import List

from lxml import etree
from pygls.lsp.types import (
    Diagnostic,
    DiagnosticRelatedInformation,
    Location,
    Position,
    Range,
)

from galaxyls.constants import DiagnosticCodes
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.xml.document import XmlDocument

EXPAND_DOCUMENT_URI_SUFFIX = "%20%28Expanded%29"


class GalaxyToolSchemaValidationService:
    """Service providing diagnostics for errors in the XML validation."""

    diagnostics_source = "Galaxy Schema Validator"

    def __init__(self, xsd_schema: etree.XMLSchema):
        """Initializes the validator"""
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

        syntax_errors = self._check_syntax(xml_document)
        if syntax_errors:
            return syntax_errors

        if not xml_document.is_tool_file:
            return []
        try:
            return self._validate(xml_document)
        except ExpandMacrosFoundException:
            return self._validate_expanded(xml_document)
        except etree.XMLSyntaxError as e:
            return self._build_diagnostics_from_syntax_error(e)

    def _check_syntax(self, xml_document: XmlDocument) -> List[Diagnostic]:
        """Check if the XML document contains any syntax error and returns it in a list.

        Args:
            document (Document): The XML document.

        Returns:
            List[Diagnostic]: The list containing the syntax error found or an empty list.
        """
        try:
            etree.fromstring(xml_document.document.source)
            return []
        except etree.XMLSyntaxError as e:
            return self._build_diagnostics_from_syntax_error(e)

    def _validate_expanded(self, xml_document: XmlDocument) -> List[Diagnostic]:
        """Validates the document after loading all the macros referenced and expands them.

        Args:
            document (Document): [description]
            xml_tree (etree.ElementTree): [description]

        Returns:
            List[Diagnostic]: [description]
        """
        try:
            if xml_document.xml_tree_expanded:
                self.xsd_schema.assertValid(xml_document.xml_tree_expanded)
            return []
        except etree.DocumentInvalid as e:
            return self._build_diagnostics_for_expanded_macros(xml_document, e)

        except etree.XMLSyntaxError as e:
            return self._build_diagnostics_for_macros_file_syntax_error(xml_document, e)

        except AssertionError as e:
            return self._build_diagnostics_for_assertion_error(xml_document, e)

    def _validate(self, xml_document: XmlDocument) -> List[Diagnostic]:
        """Validates an XML document against the XSD schema.
        Returns:
            List[Diagnostic]: The diagnosis results
        """
        try:
            if xml_document.xml_tree:
                self.xsd_schema.assertValid(xml_document.xml_tree)
            return []
        except etree.DocumentInvalid as e:
            return self._build_diagnostics(e.error_log, xml_document)

    def _build_diagnostics(self, error_log: etree._ListErrorLog, xml_document: XmlDocument) -> List[Diagnostic]:
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
                raise ExpandMacrosFoundException()

            range = xml_document.get_element_range_from_xpath_or_default(error.path)
            result = Diagnostic(
                range=range,
                message=error.message,
                source=self.diagnostics_source,
            )
            diagnostics.append(result)
        return diagnostics

    def _build_diagnostics_from_syntax_error(self, error) -> List[Diagnostic]:
        """Builds a Diagnostic element from a lxml syntax error.

        Args:
            error: The syntax error.

        Returns:
            Diagnostic: The converted Diagnostic item.
        """
        result = Diagnostic(
            range=Range(
                start=Position(line=error.lineno - 1, character=error.position[0] - 1),
                end=Position(line=error.lineno - 1, character=error.position[1] - 1),
            ),
            message=error.msg,
            source=self.diagnostics_source,
        )
        return [result]

    def _build_diagnostics_for_macros_file_syntax_error(self, xml_document: XmlDocument, syntax_error) -> List[Diagnostic]:
        tool = GalaxyToolXmlDocument.from_xml_document(xml_document)
        result = Diagnostic(
            range=tool.get_import_macro_file_range(syntax_error.filename),
            message=syntax_error.msg,
            source=self.diagnostics_source,
            related_information=[
                DiagnosticRelatedInformation(
                    message="Syntax error found on imported file.",
                    location=Location(
                        uri=Path(syntax_error.filename).as_uri(),
                        range=Range(
                            start=Position(line=syntax_error.lineno - 1, character=syntax_error.offset),
                            end=Position(line=syntax_error.lineno - 1, character=syntax_error.offset),
                        ),
                    ),
                )
            ],
        )
        return [result]

    def _build_diagnostics_for_expanded_macros(self, xml_document: XmlDocument, invalid_document_error) -> List[Diagnostic]:
        virtual_uri = xml_document.document.uri.replace("file", "gls-expand")
        diagnostics = []
        for error in invalid_document_error.error_log.filter_from_errors():
            related_info: List[DiagnosticRelatedInformation] = []
            elem_in_main_doc = xml_document.get_element_from_xpath(error.path)
            if elem_in_main_doc is None:
                elem_in_main_doc = xml_document.get_element_from_xpath("/tool/macros")
                related_info = [
                    DiagnosticRelatedInformation(
                        message=(
                            "The validation error ocurred on the expanded version of "
                            "the document, i.e. after replacing macros. "
                            "Click here to preview the expanded document."
                        ),
                        location=Location(
                            uri=f"{virtual_uri}{EXPAND_DOCUMENT_URI_SUFFIX}",
                            range=Range(
                                start=Position(line=error.line - 1, character=error.column),
                                end=Position(line=error.line - 1, character=error.column),
                            ),
                        ),
                    )
                ]
            result = Diagnostic(
                range=xml_document.get_internal_element_range_or_default(elem_in_main_doc),
                message=error.message,
                source=self.diagnostics_source,
                code=DiagnosticCodes.INVALID_EXPANDED_TOOL,
                related_information=related_info,
            )
            diagnostics.append(result)
        return diagnostics

    def _build_diagnostics_for_assertion_error(self, xml_document: XmlDocument, error: AssertionError) -> List[Diagnostic]:
        result = Diagnostic(
            range=xml_document.get_default_range(),
            message=str(error),
            source=self.diagnostics_source,
        )
        return [result]


class ExpandMacrosFoundException(Exception):
    """This exceptions indicates that the current tool contains
    macros and they should be expanded before validation.
    """
