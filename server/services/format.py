"""Service in charge of formating XML files following
best practices.
"""

from lxml import etree
from typing import List

from pygls.types import DocumentFormattingParams, Position, Range, TextEdit


class GalaxyToolFormatService:
    """Galaxy tool format service.

    This service manages XML file formatting
    following best practices for Galaxy tools.
    """

    def format(self, content: str, params: DocumentFormattingParams) -> List[TextEdit]:
        """Given the document contents returns the list of TextEdits
        needed to properly layout the document.
        """
        formatted_result = self._format_document(content, params.options.tabSize)

        lines = content.count("\n")
        start = Position(0, 0)
        end = Position(lines + 1, 0)
        return [TextEdit(Range(start, end), formatted_result)]

    def _format_document(self, content: str, tabSize: int) -> str:
        """Formats the whole XML document."""
        try:
            parser = etree.XMLParser(strip_cdata=False)
            xml = etree.fromstring(content, parser=parser)
            spaces = " " * tabSize
            etree.indent(xml, space=spaces)
            result = etree.tostring(xml, pretty_print=True, encoding=str)
            return result
        except etree.XMLSyntaxError:
            return content  # Do not auto-format if there are syntax errors
