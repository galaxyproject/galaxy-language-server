"""Utilities to validate Galaxy xml tool wrappers.
"""

from typing import List, Optional
from lxml import etree
from galaxy.util import xml_macros

from pygls.workspace import Document
from pygls.types import (
    Diagnostic,
    Position,
    Range,
)


class GalaxyToolValidationService:
    """Service providing diagnostics for errors in the XML validation."""

    def __init__(self, server_name: str, xsd_schema: etree.XMLSchema):
        """Initializes the validator"""
        self.server_name = server_name
        self.xsd_schema = xsd_schema

    def validate_document(self, document: Document) -> List[Diagnostic]:
        """Validates the Galaxy tool xml using the XSD schema (or a macro definition
        file) and returns a list of diagnotics if there are any problems.
        """
        try:
            if self._is_macro_definition_file(document):
                return self._validate_syntax(document)

            xml_tree = etree.fromstring(document.source)
            return self._validate_tree(xml_tree)
        except ExpandMacrosFoundException as e:
            return self._validate_tree_with_macros(document, e.xml_tree)
        except etree.XMLSyntaxError as e:
            return self._build_diagnostics_from_XMLSyntaxError(e)

    def _get_macros_range(
        self, document: Document, xml_tree: etree.ElementTree
    ) -> Optional[Range]:
        try:
            import_element = xml_tree.find("macros//import")
            line_number = import_element.sourceline - 1
            filename = import_element.text
            start = document.lines[line_number].find(filename)
            end = start + len(filename)
            return Range(Position(line_number, start), Position(line_number, end),)
        except BaseException:
            return None

    def _is_macro_definition_file(self, document: Document) -> bool:
        """Determines if a document is a macro definition XML and not a tool wrapper."""
        return "macros" in document.filename

    def _validate_syntax(self, document: Document) -> List[Diagnostic]:
        try:
            etree.fromstring(document.source)
        except etree.XMLSyntaxError as e:
            return self._build_diagnostics_from_XMLSyntaxError(e)
        return []

    def _validate_tree_with_macros(
        self, document: Document, xml_tree: etree.ElementTree
    ) -> List[Diagnostic]:
        try:
            error_range = self._get_macros_range(document, xml_tree)
            expanded_tool_tree, _ = xml_macros.load_with_references(document.path)
            expanded_xml = self._remove_macros(expanded_tool_tree)
            return self._validate_tree(expanded_xml)
        except etree.DocumentInvalid as e:
            return self._build_diagnostics(e.error_log)
        except etree.XMLSyntaxError as e:
            result = Diagnostic(
                error_range, f"Syntax error on macro: {e.msg}", source=self.server_name,
            )
            return [result]

    def _validate_tree(self, xml_tree: etree.ElementTree) -> List[Diagnostic]:
        """Validates an XML tree against the XSD schema.

        Args:
            xml_tree (etree.ElementTree): The root element

        Returns:
            List[Diagnostic]: The diagnosis results
        """
        try:
            self.xsd_schema.assertValid(xml_tree)
        except etree.DocumentInvalid as e:
            return self._build_diagnostics(e.error_log, xml_tree)
        return []

    def _remove_macros(self, tool_xml: etree.ElementTree) -> etree.ElementTree:
        """XSD assumes macros have been expanded, so remove them."""
        to_remove = []
        for macros_el in tool_xml.getroot().findall("macros"):
            to_remove.append(macros_el)
        for macros_el in to_remove:
            tool_xml.getroot().remove(macros_el)
        return tool_xml

    def _build_diagnostics(
        self, error_log: etree._ListErrorLog, xml_tree: Optional[etree.ElementTree] = None
    ) -> List[Diagnostic]:
        """Gets a list of Diagnostics resulting from the xml validation."""
        diagnostics = []
        for error in error_log.filter_from_errors():
            if "expand" in error.message:
                raise ExpandMacrosFoundException(xml_tree)

            result = Diagnostic(
                Range(
                    Position(error.line - 1, error.column), Position(error.line - 1, error.column),
                ),
                error.message,
                source=self.server_name,
            )
            diagnostics.append(result)

        return diagnostics

    def _build_diagnostics_from_XMLSyntaxError(self, e: etree.XMLSyntaxError) -> Diagnostic:
        """Builds a Diagnostic element from the XMLSyntaxError."""
        result = Diagnostic(
            Range(
                Position(e.lineno - 1, e.position[0] - 1),
                Position(e.lineno - 1, e.position[1] - 1),
            ),
            e.msg,
            source=self.server_name,
        )

        return [result]


class ExpandMacrosFoundException(Exception):
    """This exceptions indicates that the current tool contains
    macros and should be expanded before validation.
    """

    def __init__(self, xml_tree: Optional[etree.ElementTree] = None):
        self.xml_tree = xml_tree
