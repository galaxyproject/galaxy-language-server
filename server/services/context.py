"""This module provides a service to determine position
context inside an XML document."""

from typing import Optional
from .xsd.types import XsdTree, XsdNode


class XmlContext:
    """Represents the context at a given XML document position.

    It provides information about the current node and element
    under the cursor.
    """

    element_name: str
    node: XsdNode
    is_empty: bool

    def __init__(self, name: str = None, node: XsdNode = None):
        self.element_name = name
        self.node = node
        self.is_empty = False


class XmlContextService:
    """This service provides information about the XML context at
    a specific position of the document.
    """

    xsd_tree: XsdTree

    def __init__(self, xsd_tree: XsdTree):
        self.xsd_tree = xsd_tree

    def get_xml_context(self, xml_content: str, offset: int) -> XmlContext:
        """Gets the XML context at a given offset inside the document.

        Args:
            xml_content (str): The XML contents.
            offset (int): The character offset inside de document.

        Returns:
            XmlContext: The resulting context with the current node
            definition and other information. If the context can not be
            determined, the default context with no information is returned.
        """
        context = XmlContext()
        try:
            if self.is_empty_content(xml_content):
                context.node = self.xsd_tree.root
                context.is_empty = True
                return context

            current_tag = self.find_current_tag(xml_content, offset)
            if current_tag:
                node = self.xsd_tree.find_node_by_name(current_tag)
                return XmlContext(current_tag, node)
            return context
        except BaseException:
            return context

    @staticmethod
    def is_empty_content(xml_content: str) -> bool:
        """Determines if the given XML text is an empty document.

        Args:
            xml_content (str): The XML text.

        Returns:
            bool: True if the document is empty and False otherwise.
        """
        return xml_content.replace("<", " ").isspace()

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
        chunk = (
            chunk.replace("/", " ")
            .replace(">", " ")
            .replace("\n", " ")
            .replace("\r", "")
        )
        end = chunk.find(" ")
        if end < 0:
            end = begin
        tag = chunk[0:end]
        return tag
