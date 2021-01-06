from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, cast

from anytree import NodeMixin
from galaxyls.services.xml.constants import UNDEFINED_OFFSET
from galaxyls.services.xml.types import NodeType


class XmlSyntaxNode(ABC, NodeMixin):
    """Abtract base class that represents a syntax node in the syntax tree."""

    def __init__(self):
        self.name: Optional[str] = None
        self.start: int = UNDEFINED_OFFSET
        self.end: int = UNDEFINED_OFFSET
        self._closed: bool = False

    @property
    def is_closed(self) -> bool:
        """Indicates if this node has been closed."""
        return self._closed

    @property
    def is_element(self) -> bool:
        """Indicates if this node is an element node."""
        return self.node_type == NodeType.ELEMENT

    @property
    def is_attribute(self) -> bool:
        """Indicates if this node is an attribute node."""
        return self.node_type in [NodeType.ATTRIBUTE, NodeType.ATTRIBUTE_KEY, NodeType.ATTRIBUTE_VALUE]

    @property
    def has_attributes(self) -> bool:
        """Indicates if this node has any attributes defined."""
        return False

    @property
    def node_type(self) -> NodeType:
        """The type of this node."""
        return NodeType.UNKNOWN

    @property
    def stack(self) -> List[str]:
        """The list of names of the ancestor elements including the actual element."""
        stack = [element.name for element in self.ancestors if element.name and type(element) is XmlElement]
        if self.is_element and self.name:
            stack.append(self.name)
        return stack

    def is_at(self, offset: int) -> bool:
        """Indicates if the offset is within this node definition."""
        return self.start <= offset <= self.end

    def is_at_closing_tag(self, offset: int) -> bool:
        """Indicates if the offset is within an element's closing tag."""
        return False

    def get_attribute_nodes(self) -> List["XmlAttribute"]:
        """Gets the lists of attributes of this node if it has any."""
        return []

    def get_attribute_names(self) -> List[str]:
        """Gets the list of attribute names of this node if it has any."""
        return []

    def get_attribute_name(self) -> Optional[str]:
        """Gets the name of this attribute (if it is an attribute node)."""
        return None

    def find_node_at(self, offset: int) -> Optional["XmlSyntaxNode"]:
        """Finds the syntax node at the given document offset."""
        try:
            child = next(child for child in self.children if child.is_at(offset))
            return child.find_node_at(offset)
        except StopIteration:
            if self.is_at(offset):
                return self.find_attr_node_at(offset)
            return self

    def find_attr_node_at(self, offset: int) -> Optional["XmlSyntaxNode"]:
        """Finds the attribute node at the given document offset."""
        if self.has_attributes:
            attr_nodes = self.get_attribute_nodes()
            for attr in attr_nodes:
                if attr.is_at(offset):
                    return attr
        return self

    def get_offsets(self, _: int) -> Tuple[int, int]:
        """Get the starting and ending offsets of this syntax node as a tuple.

        Args:
            offset (int): The current document offset. Used to determine if the
            offset is currently over the starting or closing tag.

        Returns:
            Tuple[int, int]: The start and end offsets of this tag.
        """
        if self.name:
            return self.start, self.start + len(self.name)
        return self.start, self.end


class XmlContainerNode(XmlSyntaxNode):
    """Represents a node that can have content."""

    @abstractmethod
    def get_content_offsets(self) -> Tuple[int, int]:
        return NotImplemented


class XmlContent(XmlSyntaxNode):
    """Represents some content inside a XML document."""

    def __init__(self, start: int, end: int):
        super().__init__()
        self.start = start
        self.end = end

    @property
    def node_type(self) -> NodeType:
        """The type of this node."""
        return NodeType.CONTENT


class XmlAttribute(XmlSyntaxNode):
    """Represents an attribute of a XML element."""

    def __init__(self, name: str, start: int, end: int, owner: "XmlElement"):
        super().__init__()
        self.name = name
        self.start = start
        self.end = end
        self.owner = owner
        self.key = XmlAttributeKey(name, start, end, self)
        self.key.parent = self
        self.has_delimiter: bool = False
        self.value: Optional[XmlAttributeValue] = None
        self.parent = owner

    def __repr__(self) -> str:
        return f"[{self.name}={self.get_value()}]"

    @property
    def node_type(self) -> NodeType:
        """The type of this node."""
        return NodeType.ATTRIBUTE

    def set_value(self, value: Optional[str], start: int, end: int) -> None:
        """Sets the value of this attribute."""
        self.value = XmlAttributeValue(value, start, end, self)
        self.end = end
        self.value.parent = self

    def get_value(self) -> str:
        """Gets the value of this attribute (unquoted) or an empty str."""
        try:
            return self.value.unquoted
        except BaseException:
            return ""

    def get_attribute_nodes(self) -> List["XmlAttribute"]:
        """Gets the lists of attributes of this node if it has any."""
        return cast(List[XmlAttribute], self.children)

    def get_attribute_name(self) -> Optional[str]:
        """Gets the name of this attribute (if it is an attribute node)."""
        return self.name


class XmlAttributeKey(XmlSyntaxNode):
    """Represents the key (name) of a XML attribute."""

    def __init__(self, name: str, start: int, end: int, owner: XmlAttribute):
        super().__init__()
        self.name = name
        self.start = start
        self.end = end
        self.owner = owner

    @property
    def node_type(self) -> NodeType:
        """The type of this node."""
        return NodeType.ATTRIBUTE_KEY

    def get_attribute_name(self) -> Optional[str]:
        """Gets the name of this attribute (if it is an attribute node)."""
        return self.name

    def get_offsets(self, _: int) -> Tuple[int, int]:
        """Get the starting and ending offsets of this syntax node as a tuple.

        Args:
            offset (int): Not used in this override.

        Returns:
            Tuple[int, int]: The start and end offsets of this tag.
        """
        return self.start, self.end


class XmlAttributeValue(XmlSyntaxNode):
    """Represents the value of a XML attribute."""

    def __init__(self, value: Optional[str], start: int, end: int, owner: XmlAttribute):
        super().__init__()
        self.quoted = value
        self.start = start
        self.end = end
        self.owner = owner

    @property
    def node_type(self) -> NodeType:
        """The type of this node."""
        return NodeType.ATTRIBUTE_VALUE

    @property
    def unquoted(self) -> str:
        """The value without quoting marks."""
        return self.quoted.strip("\"'")

    def get_attribute_name(self) -> Optional[str]:
        """Gets the name of this attribute (if it is an attribute node)."""
        return self.owner.name


class XmlElement(XmlContainerNode):
    """Represents a XML element in the document syntax tree."""

    def __init__(self, start: int = UNDEFINED_OFFSET, end: int = UNDEFINED_OFFSET):
        super().__init__()
        self.name: Optional[str] = None
        self.start = start
        self.end = end
        self.start_tag_open_offset: int = UNDEFINED_OFFSET
        self.start_tag_close_offset: int = UNDEFINED_OFFSET
        self.end_tag_open_offset: int = UNDEFINED_OFFSET
        self.end_tag_close_offset: int = UNDEFINED_OFFSET
        self.is_self_closed: bool = False
        self.attributes: Dict[str, XmlAttribute] = {}

    def __repr__(self) -> str:
        return f"XmlElement[{self.name}]-Attrs[{','.join(self.get_attribute_names())}]"

    @property
    def node_type(self) -> NodeType:
        """The type of this node."""
        return NodeType.ELEMENT

    @property
    def has_attributes(self) -> bool:
        """Indicates if this node has any attributes defined."""
        return len(self.attributes) > 0

    @property
    def elements(self) -> List["XmlElement"]:
        """The child elements of this element."""
        return [element for element in self.children if type(element) is XmlElement]

    @property
    def end_offset(self) -> int:
        """The offset position at the end of this element"""
        if self.end_tag_close_offset != UNDEFINED_OFFSET:
            return self.end_tag_close_offset + 1  # +1 for '>'
        if self.start_tag_close_offset != UNDEFINED_OFFSET:
            return self.start_tag_close_offset + 1  # +1 for '>'
        return UNDEFINED_OFFSET

    def is_same_tag(self, tag: str) -> bool:
        """Indicates if this element has the same tag name as the one provided."""
        return self.name == tag

    def is_at(self, offset: int) -> bool:
        """Indicates if the offset is within this node definition."""
        if self.end_tag_close_offset != UNDEFINED_OFFSET:
            return self.start <= offset <= self.end_tag_close_offset
        return self.start <= offset <= self.end

    def is_at_closing_tag(self, offset: int) -> bool:
        """Indicates if the offset is within an element's closing tag."""
        return self.end_tag_open_offset <= offset <= self.end_tag_close_offset

    def get_attribute_nodes(self) -> List[XmlAttribute]:
        """Gets the lists of attributes of this node if it has any."""
        result: List[XmlAttribute] = []
        for attr in self.attributes.values():
            result.extend(attr.get_attribute_nodes())
        return result

    def get_attribute_names(self) -> List[str]:
        """Gets the list of attribute names of this node if it has any."""
        return [*self.attributes]

    def get_attribute(self, name: str) -> Optional[str]:
        """Gets the value of the attribute with the given name if it exists.

        Args:
            name (str): The name of the attribute which value will be returned.

        Returns:
            Optional[str]: The value of the attribute or None if it does not exists.
        """
        try:
            return self.attributes[name].get_value()
        except BaseException:
            return None

    def get_offsets(self, offset: int) -> Tuple[int, int]:
        """Get the starting and ending offsets of this element's name as a tuple.

        Args:
            offset (int): The current document offset. Used to determine if the
            offset is currently over the starting or closing tag.

        Returns:
            Tuple[int, int]: The start and end offsets of this tag name whitout the
            opening and ending tokens ('<', '>' '</').
        """
        if self.name:
            start = self.start + 1  # +1 for '<'
            end = start + len(self.name)
            if self.is_at_closing_tag(offset):
                start = self.end_tag_open_offset + 2  # +1 for '</'
                end = self.end_tag_close_offset
            return start, end
        return self.start, self.end

    def get_content_offsets(self) -> Tuple[int, int]:
        start = self.start_tag_close_offset + 1  # +1 for '>'
        end = self.end_tag_open_offset
        if self.is_self_closed:
            start = end = -1
        return start, end

    def get_children_with_name(self, name: str) -> List["XmlElement"]:
        children = [child for child in self.children if child.name == name]
        return list(children)

    def get_cdata_section(self) -> Optional["XmlCDATASection"]:
        """Gets the CDATA node inside this element or None if it doesn't have a CDATA section."""
        return next((node for node in self.children if type(node) == XmlCDATASection), None)


class XmlCDATASection(XmlContainerNode):
    """Represents a CDATA section in a XML document."""

    def __init__(self, start: int, end: int):
        super().__init__()
        self.start = start
        self.end = end
        self.start_content: int = UNDEFINED_OFFSET
        self.end_content: int = UNDEFINED_OFFSET

    @property
    def node_type(self) -> NodeType:
        """The type of this node."""
        return NodeType.CDATA_SECTION

    def get_content_offsets(self) -> Tuple[int, int]:
        return self.start_content, self.end_content


class XmlComment(XmlSyntaxNode):
    """Represents a comment section in a XML document."""

    def __init__(self, start: int, end: int):
        super().__init__()
        self.start = start
        self.end = end
        self.start_content: int = UNDEFINED_OFFSET
        self.end_content: int = UNDEFINED_OFFSET

    @property
    def node_type(self) -> NodeType:
        """The type of this node."""
        return NodeType.COMMENT


class XmlProcessingInstruction(XmlSyntaxNode):
    """Represents a processing instruction (like the prolog) in a XML document."""

    def __init__(self, start: int, end: int):
        super().__init__()
        self.start = start
        self.end = end
        self.start_content: int = UNDEFINED_OFFSET
        self.end_content: int = UNDEFINED_OFFSET

    @property
    def node_type(self) -> NodeType:
        """The type of this node."""
        return NodeType.PROCESSING_INSTRUCTION
