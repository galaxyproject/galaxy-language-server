from typing import Dict, List, Optional
from pygls.types import Position


class XmlSyntaxToken:
    def __init__(self):
        self.start: Position = Position()
        self.end: Position = Position()


class XmlNodeContent(XmlSyntaxToken):
    def __init__(self, start: Position, end: Position):
        super().__init__()
        self.start = start
        self.end = end
        self.is_cdata: bool


class XmlAttribute(XmlSyntaxToken):
    def __init__(self, name: str, start: Position, value: Optional[str] = None):
        super().__init__()
        self.key = XmlAttributeKey(name, start)
        self.value = XmlAttributeValue(value, self.key.end)
        self.start = start
        self.end = self.value.end


class XmlAttributeKey(XmlSyntaxToken):
    def __init__(self, name: str, start: Position):
        super().__init__()
        self.name = name
        self.start = start
        self.end = Position(start.line, start.character + len(name))


class XmlAttributeValue(XmlSyntaxToken):
    def __init__(self, value: Optional[str], start: Position):
        super().__init__()
        self.value = value
        self.start = start
        if value:
            self.end = Position(start.line, start.character + len(value))
        else:
            self.end = start


class XmlElement(XmlSyntaxToken):
    def __init__(self, start: Position, name: str = "", parent: Optional["XmlElement"] = None):
        super().__init__()
        self.name = name
        self.start = start
        if name:
            self.end = Position(start.line, start.character + len(name))
        else:
            self.end = start
        self.start_tag_end: Optional[Position] = None
        self.end_tag_start: Optional[Position] = None
        self.attributes: Dict[str, XmlAttribute] = {}
        self.parent: Optional[XmlElement] = parent
        self.children: List[XmlElement] = []

    def __str__(self) -> str:
        return self.name

    @property
    def closed(self) -> bool:
        return self.end_tag_start is not None
