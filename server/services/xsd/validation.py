"""Utilities to validate Galaxy xml tool wrappers.
"""

from typing import List
from lxml import etree

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

    def validate_xml(self, source: str) -> List[Diagnostic]:
        """Validates the Galaxy tool xml using the XSD schema and returns a list
        of diagnotics if there are any problems.
        """
        try:
            xml = etree.fromstring(source)
            self.xsd_schema.assertValid(xml)
        except etree.DocumentInvalid as e:
            return self._build_diagnostics(e.error_log)
        except etree.XMLSyntaxError as e:
            return self._build_diagnostics_from_XMLSyntaxError(e)

        return []

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
