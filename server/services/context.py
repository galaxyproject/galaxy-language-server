"""This module provides a service to determine position
context inside an XML document."""

from typing import Optional, List
from .xsd.types import XsdTree, XsdNode
from lxml import etree
from io import BytesIO
from pygls.workspace import Document, Position

START_TAG_EVENT = "start"
END_TAG_EVENT = "end"


class XmlElement:
    tag: str
    tag_position: Position
    tag_offset: int
    element: etree.Element

    def __init__(self, tag: str, line: int, character: int):
        self.tag = tag
        self.tag_position = Position(line, character)
        self.tag_offset = -1
        self.element


class XmlContext:
    """Represents the context at a given XML document position.

    It provides information about the current node and element
    under the cursor.
    """

    element_name: str
    node: XsdNode
    is_empty: bool

    is_tag: bool
    is_attribute: bool
    is_content: bool

    def __init__(self, name: str = None, node: XsdNode = None):
        self.element_name = name
        self.node = node
        self.is_empty = False
        self.is_tag = False
        self.is_attribute = False


class XmlContextService:
    """This service provides information about the XML context at
    a specific position of the document.
    """

    xsd_tree: XsdTree

    def __init__(self, xsd_tree: XsdTree):
        self.xsd_tree = xsd_tree

    def get_xml_context(self, document: Document, position: Position) -> XmlContext:
        """Gets the XML context at a given offset inside the document.

        Args:
            document (Document): The current document.
            position (Position): The position inside de document.

        Returns:
            XmlContext: The resulting context with the current node
            definition and other information. If the context can not be
            determined, the default context with no information is returned.
        """
        context = XmlContext()
        if self.is_empty_content(document):
            context.node = self.xsd_tree.root
            context.is_empty = True
            return context

        xml_content = document.source
        offset = document.offset_at_position(position)
        current_tag = self.find_current_tag(xml_content, offset)
        if current_tag:
            node = self.xsd_tree.find_node_by_name(current_tag)
            return XmlContext(current_tag, node)
        return context

    @staticmethod
    def is_empty_content(document: Document) -> bool:
        """Determines if the given XML document is an empty document.

        Args:
            document (Document): The document to check.

        Returns:
            bool: True if the document is empty and False otherwise.
        """
        xml_content = document.source.strip()
        return not xml_content or len(xml_content) < 2

    @staticmethod
    def find_current_tag(content: str, offset: int) -> Optional[str]:
        """Tries to find the tag name at the given offset of the XML document.

        The document may be incomplete or invalid so the parsing can not
        rely on well-formed documents.

        Args:
            content (str): The text content of the document.
            offset (int): The offset character position on the document.

        Returns:
            Optional[str]: The name of the XML tag at the given offset
            in the document.
        """
        begin = content.rfind("<", 0, offset)
        if begin < 0:
            return None
        begin = begin + 1  # skip <
        chunk = content[begin:]
        close_pos = content.rfind("/>", begin, offset)
        while close_pos > 0:
            begin = content.rfind("<", 0, begin - 1)
            if begin < 0:
                return None
            begin = begin + 1  # skip <
            chunk = content[begin:close_pos]
            close_pos = chunk.rfind("/>")
        chunk = chunk.replace("/", " ").replace(">", " ").replace("\n", " ").replace("\r", "")
        end = chunk.find(" ")
        if end < 0:
            end = len(chunk)
        tag = chunk[0:end]
        return tag

    @staticmethod
    def is_inside_attr_value(content: str, offset: int) -> bool:
        tag_start = content.rfind("<", 0, offset)
        attr_value_start = content.rfind('="', 0, offset)
        return attr_value_start > tag_start


class XmlContextParser:

    _current_element: Optional[XmlElement]
    _content_lines: List[str]
    _element_stack: List[XmlElement]

    def __init__(self):
        self._current_element = None
        self._content_lines = []
        self._element_stack = []
        pass

    def parse(self, xml_content: str, offset: int):
        self._content_lines = xml_content.split("\n")
        source = BytesIO(xml_content.encode())

        for event, element in etree.iterparse(source, recover=True):
            if event == END_TAG_EVENT:
                character = self._find_tag_start_at_line_number(
                    xml_content, element.tag, element.sourceline
                )
                xml_element = XmlElement(element.tag, element.sourceline, character)
                xml_element.internal = element
                self._current_element = xml_element
            else:
                print(event)

    def _find_tag_start_at_line_number(self, xml_content: str, tag: str, line_number: int):
        line = self._content_lines[line_number - 1]
        start_position = line.find(tag)
        return start_position
