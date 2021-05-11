"""This module provides a service to determine position context inside an XML document."""

from typing import List, Optional, cast

from pygls.lsp.types import Range
from pygls.workspace import Position

from galaxyls.services.tools.constants import MACROS
from galaxyls.services.xml.constants import UNDEFINED_OFFSET
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.nodes import XmlElement, XmlSyntaxNode
from galaxyls.services.xml.types import NodeType
from galaxyls.services.xml.utils import convert_document_offsets_to_range
from galaxyls.services.xsd.types import XsdNode, XsdTree


class XmlContext:
    """Represents the context at a given XML document position.

    It provides information about the token under the cursor and
    the XSD node definition associated.
    """

    def __init__(
        self,
        xml_document: XmlDocument,
        xsd_node: Optional[XsdNode],
        node: Optional[XmlSyntaxNode] = None,
        line_text: str = "",
        position: Optional[Position] = None,
        offset: int = UNDEFINED_OFFSET,
    ):
        self.xml_document = xml_document
        self._xsd_node = xsd_node
        self._node = node
        self._line_text = line_text
        self._position = position
        self._offset = offset

    @property
    def node(self) -> Optional[XmlSyntaxNode]:
        """The syntax node at the context position."""
        return self._node

    @property
    def position(self) -> Optional[Position]:
        """The context position (line and character) inside de Document."""
        return self._position

    @property
    def offset(self) -> int:
        """The character offset inside de Document."""
        return self._offset

    @property
    def line_text(self) -> str:
        """The text contents of the document line at the context position."""
        return self._line_text

    @property
    def characted_at_position(self) -> Optional[str]:
        """The character at the context position."""
        try:
            return self._line_text[self._position.character]
        except (IndexError, AttributeError):
            return None

    @property
    def xsd_element(self) -> Optional[XsdNode]:
        """The XSD element associated with the token in context."""
        return self._xsd_node

    @property
    def is_empty(self) -> bool:
        """Indicates if the document is empty and no context can be determined."""
        return not self._node

    @property
    def is_root(self) -> bool:
        """Indicates if the element at context is the root element."""
        return self._node is not None and len(self._node.ancestors) == 1

    @property
    def is_tag(self) -> bool:
        """Indicates if the token in context is a tag."""
        return self._node is not None and self._node.node_type == NodeType.ELEMENT

    @property
    def is_tag_name(self) -> bool:
        """Indicates if the token in context is a start tag name."""
        return (
            self.is_tag
            and cast(XmlElement, self._node).name_start_offset <= self._offset <= cast(XmlElement, self._node).name_end_offset
        )

    @property
    def is_attribute(self) -> bool:
        """Indicates if the token in context is an attribute."""
        return self._node is not None and self._node.is_attribute

    @property
    def is_attribute_key(self) -> bool:
        """Indicates if the token in context is an attribute key."""
        return self._node is not None and self._node.node_type == NodeType.ATTRIBUTE_KEY

    @property
    def is_attribute_value(self) -> bool:
        """Indicates if the token in context is an attribute value."""
        return self._node is not None and self._node.node_type == NodeType.ATTRIBUTE_VALUE

    @property
    def is_inside_attribute_value(self) -> bool:
        """Indicates if the token in context is an attribute value."""
        return self.is_attribute_value and self.offset > self.node.start and self.offset < self.node.end

    @property
    def is_attribute_end(self) -> bool:
        """Indicates that the context position is at the ending quote character of an attribute.

        Example: <tag attribute="value["] <- The context position is at " """
        return self.is_attribute_value and self._offset == self._node.end - 1

    @property
    def attribute_name(self) -> Optional[str]:
        """The name of the attribute if the context is an attribute or None."""
        return self._node and self._node.get_attribute_name()

    @property
    def is_content(self) -> bool:
        """Indicates if the token in context is within a content or CDATA block."""
        return self._node is not None and self._node.node_type in [NodeType.CONTENT, NodeType.CDATA_SECTION]

    @property
    def is_closing_tag(self) -> bool:
        """Indicates if the token in context is a closing tag."""
        return self._node is not None and self._node.is_at_closing_tag(self._offset)

    @property
    def is_at_end(self) -> bool:
        """Indicates if the context is at the last character of the node."""
        return self._node is not None and self._node.end == self._offset

    @property
    def stack(self) -> List[str]:
        """The list of XML tag names from the root to the token in context."""
        if not self._node:
            return []
        return self._node.stack

    def has_reached_max_occurs(self, node: XsdNode) -> bool:
        """Checks if the given node has reached the maximum number
        of occurrences.

        Args:
            child (XsdNode): The node to check.

        Returns:
            bool: True if the node has reached the maximum number
            of occurrences permitted.
        """
        if node.max_occurs < 0:
            return False
        target = self._node.parent or self._node
        if target:
            existing_count = sum(1 for child_node in target.children if child_node.name == node.name)
            return existing_count >= node.max_occurs
        return False

    def is_valid_tag(self) -> bool:
        """Indicates"""
        if self.is_tag and self._xsd_node is not None:
            return self._node.name == self._xsd_node.name or self._node.name in [node.name for node in self._xsd_node.children]
        return False


class XmlContextService:
    """This service provides information about the XML context at
    a specific position of the document.
    """

    def __init__(self, xsd_tree: XsdTree):
        self.xsd_tree = xsd_tree

    def get_xml_context(self, xml_document: XmlDocument, position: Position) -> XmlContext:
        """Gets the XML context at a given position inside the document.

        Args:
            document (Document): The current document.
            position (Position): The position inside de document.

        Returns:
            XmlContext: The resulting context with the current node
            definition and other information. If the context can not be
            determined, the default context with no information is returned.
        """
        offset = xml_document.document.offset_at_position(position)

        if xml_document.is_empty:
            return XmlContext(xml_document, self.xsd_tree.root, node=None)
        node = xml_document.get_node_at(offset)
        xsd_node = self.find_matching_xsd_element(node, self.xsd_tree)
        line_text = xml_document.document.lines[position.line]
        context = XmlContext(xml_document, xsd_node, node, line_text, position, offset)
        return context

    def find_matching_xsd_element(self, node: Optional[XmlSyntaxNode], xsd_tree: XsdTree) -> Optional[XsdNode]:
        """Finds the xsd element in the XSD tree that matches the xml element associated with the given syntax node.
        If there is no matching node, the root (tool) xsd node is always returned.

        Args:
            node (XmlSyntaxNode): The syntax node to match.
            xsd_tree (XsdTree): The XSD tree definition.

        Returns:
            XsdNode: The matching xsd node or None if there is no matching.
        """
        if node:
            node_stack = node.stack
            if len(node_stack) > 0 and MACROS in node_stack:
                return xsd_tree.find_node_by_name(node_stack[-1])
            xsd_node = xsd_tree.find_node_by_stack(node_stack)
            if xsd_node is None:
                xsd_node = xsd_tree.find_node_by_stack(node_stack[:-1])
            return xsd_node

    def get_range_for_context(self, xml_document: XmlDocument, context: XmlContext) -> Range:
        start_offset, end_offset = context.node.get_offsets(context.offset)
        return convert_document_offsets_to_range(xml_document.document, start_offset, end_offset)
