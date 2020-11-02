from typing import Dict, List, Optional

from anytree import NodeMixin
from pygls.workspace import Document

from .constants import UNDEFINED_OFFSET
from .types import DocumentType, NodeType


class XmlSyntaxNode(NodeMixin):
    def __init__(self):
        self.name: Optional[str] = None
        self.start: int = UNDEFINED_OFFSET
        self.end: int = UNDEFINED_OFFSET
        self._closed: bool = False

    def __str__(self) -> str:
        return f"{self.node_type} ({self.name})"

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


class XmlContent(XmlSyntaxNode):
    def __init__(self, start: int, end: int):
        super().__init__()
        self.start = start
        self.end = end

    @property
    def node_type(self) -> NodeType:
        return NodeType.CONTENT


class XmlAttribute(XmlSyntaxNode):
    def __init__(self, name: str, start: int, end: int, owner_element: "XmlElement"):
        super().__init__()
        self.name = name
        self.start = start
        self.end = end
        self.owner_element = owner_element
        self.key = XmlAttributeKey(name, start, end)
        self.has_delimiter: bool = False
        self.value: Optional[XmlAttributeValue] = None

    @property
    def node_type(self) -> NodeType:
        return NodeType.ATTRIBUTE

    def set_value(self, value: Optional[str], start: int, end: int) -> None:
        self.value = XmlAttributeValue(value, start, end)


class XmlAttributeKey(XmlSyntaxNode):
    def __init__(self, name: str, start: int, end: int):
        super().__init__()
        self.name = name
        self.start = start
        self.end = end

    @property
    def node_type(self) -> NodeType:
        return NodeType.ATTRIBUTE_KEY


class XmlAttributeValue(XmlSyntaxNode):
    def __init__(self, value: Optional[str], start: int, end: int):
        super().__init__()
        self.quoted = value
        self.start = start
        self.end = end

    @property
    def node_type(self) -> NodeType:
        return NodeType.ATTRIBUTE_VALUE

    @property
    def unquoted(self) -> str:
        return self.quoted.strip("\"'")


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


class XmlCDATASection(XmlSyntaxNode):
    def __init__(self, start: int, end: int):
        super().__init__()
        self.start = start
        self.end = end
        self.start_content: int = UNDEFINED_OFFSET
        self.end_content: int = UNDEFINED_OFFSET

    def node_type(self) -> NodeType:
        return NodeType.CDATA_SECTION


class XmlComment(XmlSyntaxNode):
    def __init__(self, start: int, end: int):
        super().__init__()
        self.start = start
        self.end = end
        self.start_content: int = UNDEFINED_OFFSET
        self.end_content: int = UNDEFINED_OFFSET

    def node_type(self) -> NodeType:
        return NodeType.COMMENT


class XmlDocument(XmlSyntaxNode):
    def __init__(self, document: Document):
        super().__init__()
        self.document: Document = document

    @property
    def root(self) -> Optional[XmlElement]:
        if len(self.children) == 0:
            return None
        return next(child for child in self.children if type(child) == XmlElement)

    @property
    def document_type(self) -> DocumentType:
        try:
            if self.root.name == "tool":
                return DocumentType.TOOL
            if self.root.name == "macros":
                return DocumentType.MACROS
        except BaseException:
            pass
        return DocumentType.UNKNOWN
