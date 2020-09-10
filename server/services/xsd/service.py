"""Utilities to validate Galaxy xml tool wrappers and extract
information from the XSD schema.
"""

from typing import List
from lxml import etree

from pygls.types import (
    Diagnostic,
    MarkupContent,
    Position,
    Range,
)

from .constants import TOOL_XSD_FILE, MSG_NO_DOCUMENTATION_AVAILABLE
from .parser import GalaxyToolXsdParser


class GalaxyToolXsdService:
    """Galaxy tool Xml Schema Definition service.

    This service provides functionality to extract information from
    the XSD schema and validate XML files against it.
    """

    def __init__(self, server_name: str):
        """Initializes the validator by loading the XSD."""
        self.server_name = server_name
        self.xsd_doc = etree.parse(str(TOOL_XSD_FILE))
        self.xsd_schema = etree.XMLSchema(self.xsd_doc)
        self.xsd_parser = GalaxyToolXsdParser(self.xsd_doc.getroot())

    def validate_xml(self, source: str) -> List[Diagnostic]:
        """Validates the Galaxy tool xml using the XSD schema and returns a list
        of diagnotics if there are any problems.
        """
        diagnostics = []
        try:
            xml = etree.fromstring(source)
            self.xsd_schema.assertValid(xml)
        except etree.DocumentInvalid as e:
            diagnostics = self._build_diagnostics(e.error_log)
        except etree.XMLSyntaxError as e:
            diagnostics = self._build_diagnostics_from_XMLSyntaxError(e)

        return diagnostics

    def get_documentation_for(self, element_name: str) -> MarkupContent:
        """Gets the documentation annotated in the XSD about the
        given element name (node or attribute).
        """
        tree = self.xsd_parser.get_tree()
        element = tree.find_node_by_name(element_name)
        if element is None:
            return MSG_NO_DOCUMENTATION_AVAILABLE
        return element.get_doc()

    def _build_diagnostics(self, error_log: etree._ListErrorLog) -> List[Diagnostic]:
        """Gets a list of Diagnostics resulting from the xml validation."""
        diagnostics = []
        for error in error_log.filter_from_errors():
            # Macro validation may get a bit complex, for the
            # moment just skip macro expansion
            if "expand" in error.message:
                continue

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
