from typing import Dict, List, Optional, cast

from anytree import NodeMixin

from .constants import UNDEFINED_OFFSET
from .types import NodeType


class XmlSyntaxNode(NodeMixin):
    def __init__(self):
        self.name: Optional[str] = None
        self.start: int = UNDEFINED_OFFSET
        self.end: int = UNDEFINED_OFFSET
        self._closed: bool = False

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def is_element(self) -> bool:
        return self.node_type == NodeType.ELEMENT

    @property
    def has_attributes(self) -> bool:
        return False

    @property
    def node_type(self) -> NodeType:
        return NodeType.UNKNOWN

    @property
    def stack(self) -> List[str]:
        stack = [element.name for element in self.ancestors if element.name and type(element) is XmlElement]
        if self.is_element and self.name:
            stack.append(self.name)
        return stack

    def is_at(self, offset: int) -> bool:
        return self.start <= offset <= self.end

    def is_at_closing_tag(self, offset: int) -> bool:
        return False

    def get_attribute_nodes(self) -> List["XmlSyntaxNode"]:
        return []

    def get_attribute_names(self) -> List[str]:
        return []

    def get_attribute_name(self) -> Optional[str]:
        return None

    def find_node_at(self, offset: int) -> Optional["XmlSyntaxNode"]:
        try:
            child = next(child for child in self.children if child.is_at(offset))
            return child.find_node_at(offset)
        except StopIteration:
            if self.is_at(offset):
                return self.find_attr_node_at(offset)
            return self

    def find_attr_node_at(self, offset: int) -> Optional["XmlSyntaxNode"]:
        if self.has_attributes:
            attr_nodes = self.get_attribute_nodes()
            for attr in attr_nodes:
                if attr.is_at(offset):
                    return attr
        return self


class XmlContent(XmlSyntaxNode):
    def __init__(self, start: int, end: int):
        super().__init__()
        self.start = start
        self.end = end

    @property
    def node_type(self) -> NodeType:
        return NodeType.CONTENT


class XmlAttribute(XmlSyntaxNode):
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

    @property
    def node_type(self) -> NodeType:
        return NodeType.ATTRIBUTE

    def set_value(self, value: Optional[str], start: int, end: int) -> None:
        self.value = XmlAttributeValue(value, start, end, self)
        self.end = end
        self.value.parent = self

    def get_attribute_nodes(self) -> List["XmlSyntaxNode"]:
        return cast(List[XmlSyntaxNode], self.children)

    def get_attribute_name(self) -> Optional[str]:
        return self.name


class XmlAttributeKey(XmlSyntaxNode):
    def __init__(self, name: str, start: int, end: int, owner: XmlAttribute):
        super().__init__()
        self.name = name
        self.start = start
        self.end = end
        self.owner = owner

    @property
    def node_type(self) -> NodeType:
        return NodeType.ATTRIBUTE_KEY

    def get_attribute_name(self) -> Optional[str]:
        return self.name


class XmlAttributeValue(XmlSyntaxNode):
    def __init__(self, value: Optional[str], start: int, end: int, owner: XmlAttribute):
        super().__init__()
        self.quoted = value
        self.start = start
        self.end = end
        self.owner = owner

    @property
    def node_type(self) -> NodeType:
        return NodeType.ATTRIBUTE_VALUE

    @property
    def unquoted(self) -> str:
        return self.quoted.strip("\"'")

    def get_attribute_name(self) -> Optional[str]:
        return self.owner.name


class XmlElement(XmlSyntaxNode):
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

    @property
    def node_type(self) -> NodeType:
        return NodeType.ELEMENT

    @property
    def has_attributes(self) -> bool:
        return len(self.attributes) > 0

    @property
    def elements(self) -> List["XmlElement"]:
        return [element for element in self.children if type(element) is XmlElement]

    def is_same_tag(self, tag: str) -> bool:
        return self.name == tag

    def is_at_closing_tag(self, offset: int) -> bool:
        return self.end_tag_open_offset <= offset <= self.end_tag_close_offset

    def get_attribute_nodes(self) -> List[XmlSyntaxNode]:
        result: List[XmlSyntaxNode] = []
        for attr in self.attributes.values():
            result.extend(attr.get_attribute_nodes())
        return result

    def get_attribute_names(self) -> List[str]:
        return [*self.attributes]


class XmlCDATASection(XmlSyntaxNode):
    def __init__(self, start: int, end: int):
        super().__init__()
        self.start = start
        self.end = end
        self.start_content: int = UNDEFINED_OFFSET
        self.end_content: int = UNDEFINED_OFFSET

    @property
    def node_type(self) -> NodeType:
        return NodeType.CDATA_SECTION


class XmlComment(XmlSyntaxNode):
    def __init__(self, start: int, end: int):
        super().__init__()
        self.start = start
        self.end = end
        self.start_content: int = UNDEFINED_OFFSET
        self.end_content: int = UNDEFINED_OFFSET

    @property
    def node_type(self) -> NodeType:
        return NodeType.COMMENT


class XmlProcessingInstruction(XmlSyntaxNode):
    def __init__(self, start: int, end: int):
        super().__init__()
        self.start = start
        self.end = end
        self.start_content: int = UNDEFINED_OFFSET
        self.end_content: int = UNDEFINED_OFFSET

    @property
    def node_type(self) -> NodeType:
        return NodeType.PROCESSING_INSTRUCTION
