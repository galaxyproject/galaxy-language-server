"""Service in charge of formating XML files following
best practices.
"""

from lxml import etree
from typing import List, cast

from pygls.lsp.types import DocumentFormattingParams, Position, Range, TextEdit

DEFAULT_INDENTATION = " " * 4


class GalaxyToolFormatService:
    """Galaxy tool format service.

    This service manages XML file formatting
    following best practices for Galaxy tools.
    """

    def format(self, content: str, params: DocumentFormattingParams) -> List[TextEdit]:
        """Given the document contents returns the list of TextEdits
        needed to properly layout the document.
        """
        formatted_result = self.format_content(content, params.options.tab_size)

        lines = content.count("\n")
        start = Position(line=0, character=0)
        end = Position(line=lines + 1, character=0)
        return [TextEdit(range=Range(start=start, end=end), new_text=formatted_result)]

    def format_content(self, content: str, tabSize: int = 4) -> str:
        """Formats the given XML content."""
        try:
            parser = etree.XMLParser(strip_cdata=False)
            xml = etree.fromstring(content, parser=parser)
            spaces = " " * tabSize
            etree.indent(xml, space=spaces)
            result = etree.tostring(xml, pretty_print=True, encoding=str)
            return cast(str, result)
        except etree.XMLSyntaxError:
            return content  # Do not auto-format if there are syntax errors
