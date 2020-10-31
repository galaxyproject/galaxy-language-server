from pygls.workspace import Document
from typing import Optional
from .utils import MultiLineStream
from .types import XmlDocument


class XmlDocumentParser:
    def parse(self, document: Document) -> XmlDocument:
        raise NotImplementedError


class TolerantXmlDocumentParser(XmlDocumentParser):
    def __init__(self) -> None:
        self.stream: Optional[MultiLineStream] = None

    def parse(self, document: Document) -> XmlDocument:
        stream = MultiLineStream(document.source)

        raise NotImplementedError

    def next_element_name(self) -> str:
        return self.stream.advance_if_regex(r"^[_:\w][_:\w-.\d]*")

    def next_attribute_name(self) -> str:
        return self.stream.advance_if_regex(r"^[^\s\"'></=\x00-\x0F\x7F\x80-\x9F]*")
