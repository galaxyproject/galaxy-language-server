"""Utilities to validate Galaxy xml tool wrappers.
"""

from typing import List
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

    def validate_xml(self, document: Document) -> List[Diagnostic]:
        """Validates the Galaxy tool xml using the XSD schema and returns a list
        of diagnotics if there are any problems.
        """
        try:
            xml_tree = etree.fromstring(document.source)
            return self._validate_tree(xml_tree)
        except ExpandMacrosFoundException:
            return self._validate_with_macros(document)

    def _validate_with_macros(self, document: Document) -> List[Diagnostic]:
        try:
            expanded_tool_tree, _ = xml_macros.load_with_references(document.path)
            expanded_xml = self._remove_macros(expanded_tool_tree)
            return self._validate_tree(expanded_xml)
        except etree.DocumentInvalid as e:
            return self._build_diagnostics(e.error_log)
        except etree.XMLSyntaxError as e:
            return self._build_diagnostics_from_XMLSyntaxError(e)

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
            return self._build_diagnostics(e.error_log)
        except etree.XMLSyntaxError as e:
            return self._build_diagnostics_from_XMLSyntaxError(e)
        return []

    def _remove_macros(self, tool_xml: etree.ElementTree) -> etree.ElementTree:
        """XSD assumes macros have been expanded, so remove them."""
        to_remove = []
        for macros_el in tool_xml.getroot().findall("macros"):
            to_remove.append(macros_el)
        for macros_el in to_remove:
            tool_xml.getroot().remove(macros_el)
        return tool_xml

    def _build_diagnostics(self, error_log: etree._ListErrorLog) -> List[Diagnostic]:
        """Gets a list of Diagnostics resulting from the xml validation."""
        diagnostics = []
        for error in error_log.filter_from_errors():
            if "expand" in error.message:
                raise ExpandMacrosFoundException()

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

    pass
