"""
Utilities to validate Galaxy xml tool wrappers and extract
information from the XSD schema.
"""

import os
from typing import Optional, List
from lxml import etree

from pygls.types import (
    Diagnostic,
    Position,
    Range,
)

TOOL_XSD = os.path.join(os.path.dirname(__file__), 'xsd', "galaxy.xsd")


class GalaxyToolXsdValidator():
    """Galaxy tool validator based on XSD Schema."""

    def __init__(self, server_name: str):
        """Initializes the validator by loading the XSD."""
        self.server_name = server_name
        self.xsd_doc = etree.parse(TOOL_XSD)
        self.xsd_schema = etree.XMLSchema(self.xsd_doc)

    def validate_xml(self, source: str) -> List[Diagnostic]:
        """Validates the Galaxy tool xml using the XSD schema and returns a list
        of diagnotics if there are any problems."""
        diagnostics = []
        try:
            xml = etree.fromstring(source)
            self.xsd_schema.assertValid(xml)
        except etree.DocumentInvalid as e:
            diagnostics = self._build_diagnostics(e.error_log)
        except etree.XMLSyntaxError as e:
            diagnostics = self._build_diagnostics_from_XMLSyntaxError(e)

        return diagnostics

    def get_documentation_for(self, element: str) -> str:
        """Gets the documentation annotated in the XSD about the given element."""
        try:
            value = self.xsd_doc.xpath(
                ".//*[@name=$elem]/xs:annotation/xs:documentation/text()",
                namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'},
                elem=element)
            return value[0]
        except:
            return "No documentation available"

    def _build_diagnostics(self, error_log: etree._ListErrorLog) -> List[Diagnostic]:
        """Gets a list of Diagnostics resulting from the xml validation."""
        diagnostics = []
        for error in error_log.filter_from_errors():
            # Macro validation may get a bit complex, for the moment just skip macro expansion
            if "expand" in error.message:
                continue

            result = Diagnostic(
                Range(
                    Position(error.line - 1, error.column),
                    Position(error.line - 1, error.column)
                ),
                error.message,
                source=self.server_name
            )
            diagnostics.append(result)

        return diagnostics

    def _build_diagnostics_from_XMLSyntaxError(self, e: etree.XMLSyntaxError) -> Diagnostic:
        """Builds a Diagnostic element from the XMLSyntaxError."""
        result = Diagnostic(
            Range(
                Position(e.lineno - 1, e.position[0]-1),
                Position(e.lineno - 1, e.position[1]-1)
            ),
            e.msg,
            source=self.server_name
        )

        return [result]
