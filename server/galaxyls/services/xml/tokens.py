from .types import DocumentType, NodeType
from typing import Dict, Optional
from anytree import NodeMixin
from pygls.workspace import Document


class XmlSyntaxNode(NodeMixin):
    def __init__(self):
        self.start: int = -1
        self.end: int = -1
        self._closed = False

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def is_element(self) -> bool:
        return self.get_node_type() == NodeType.ELEMENT

    @property
    def has_attributes(self) -> bool:
        return False

    def get_node_type(self) -> NodeType:
        raise NotImplementedError


class XmlContent(XmlSyntaxNode):
    def __init__(self, start: int, end: int):
        super().__init__()
        self.start = start
        self.end = end

    def get_node_type(self) -> NodeType:
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

    def get_node_type(self) -> NodeType:
        return NodeType.ATTRIBUTE

    def set_value(self, value: Optional[str], start: int, end: int) -> None:
        self.value = XmlAttributeValue(value, start, end)


class XmlAttributeKey(XmlSyntaxNode):
    def __init__(self, name: str, start: int, end: int):
        super().__init__()
        self.name = name
        self.start = start
        self.end = end

    def get_node_type(self) -> NodeType:
        return NodeType.ATTRIBUTE_KEY


class XmlAttributeValue(XmlSyntaxNode):
    def __init__(self, value: Optional[str], start: int, end: int):
        super().__init__()
        self.value = value
        self.start = start
        self.end = end

    def get_node_type(self) -> NodeType:
        return NodeType.ATTRIBUTE_VALUE


class XmlElement(XmlSyntaxNode):
    def __init__(self, start: int, end: int):
        super().__init__()
        self.name: Optional[str] = None
        self.start = start
        self.end = end
        self.start_tag_open_offset: Optional[int] = None
        self.start_tag_close_offset: Optional[int] = None
        self.end_tag_open_offset: Optional[int] = None
        self.end_tag_close_offset: Optional[int] = None
        self.is_self_closed: bool = False
        self.attributes: Dict[str, XmlAttribute] = {}

    def __str__(self) -> str:
        return self.name or ""

    def get_node_type(self) -> NodeType:
        return NodeType.ELEMENT

    def is_same_tag(self, tag: str) -> bool:
        return self.name == tag

    @property
    def has_attributes(self) -> bool:
        return len(self.attributes) > 0


class XmlCDATASection(XmlSyntaxNode):
    def __init__(self, start: int, end: int):
        super().__init__()
        self.start = start
        self.end = end
        self.start_content: int = -1
        self.end_content: int = -1

    def get_node_type(self) -> NodeType:
        return NodeType.CDATA_SECTION


class XmlComment(XmlSyntaxNode):
    def __init__(self, start: int, end: int):
        super().__init__()
        self.start = start
        self.end = end
        self.start_content: int = -1
        self.end_content: int = -1

    def get_node_type(self) -> NodeType:
        return NodeType.COMMENT


class XmlDocument(XmlSyntaxNode):
    def __init__(self, document: Document):
        self.document = document
        self.type = DocumentType.UNKNOWN
