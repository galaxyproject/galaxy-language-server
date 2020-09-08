"""This module provides a service to determine position
context inside an XML document."""

from typing import Optional, List
from .xsd.types import XsdTree, XsdNode
from io import BytesIO
from pygls.workspace import Document, Position
import xml.sax

START_TAG_EVENT = "start"
END_TAG_EVENT = "end"


class XmlContext:
    """Represents the context at a given XML document position.

    It provides information about the current node and element
    under the cursor.
    """

    def __init__(
        self,
        name: str = None,
        node: XsdNode = None,
        position: Position = Position(),
        document_line: str = "",
    ):
        self.token_name: str = name
        self.node: XsdNode = node
        self.target_position: Position = position
        self.document_line: str = document_line
        self.is_empty: bool = False
        self.is_tag: bool = False
        self.is_attribute: bool = False
        self.stack: List[str] = []


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
    def __init__(self):
        self._document: Document = None

    def parse(self, document: Document, position: Position) -> XmlContext:
        self._document = document
        source = BytesIO(document.source.encode())
        context_line = document.lines[position.line]
        context = XmlContext(document_line=context_line, position=position)

        reader = self._build_xml_reader()
        locator = xml.sax.expatreader.ExpatLocator(reader)
        content_handler = ContextBuilderContentHandler(locator, context)
        error_handler = MyErrorHandler(context)
        reader.setContentHandler(content_handler)
        reader.setErrorHandler(error_handler)
        try:
            reader.parse(source)
        except ContextFoundException:
            pass  # All is good, we got what we needed

        return context

    def _build_xml_reader(self) -> xml.sax.xmlreader.XMLReader:
        reader = xml.sax.make_parser()
        reader.setFeature(xml.sax.handler.feature_namespaces, False)
        reader.setFeature(xml.sax.handler.feature_validation, False)
        return reader


class ContextBuilderContentHandler(xml.sax.ContentHandler):
    def __init__(self, locator, context: XmlContext):
        xml.sax.ContentHandler.__init__(self)
        self._loc = locator
        self._context: XmlContext = context
        self.setDocumentLocator(self._loc)

    def startDocument(self):
        pass

    def endDocument(self):
        pass

    def startElement(self, tag, attributes):
        self._context.stack.append(tag)
        current_position = self.get_current_position()

        if current_position.line == self._context.target_position.line:
            target_offset = self._context.target_position.character
            tag_offset = current_position.character + len(tag)
            is_on_tag = current_position.character < target_offset <= tag_offset
            if is_on_tag:
                self._context.is_tag = True
                self._context.token_name = tag
                raise ContextFoundException()

            accum = 0
            for attr_name, attr_value in attributes.items():
                attr_start = tag_offset + accum + 2  # +2 for '<' and ' '
                attr_end = attr_start + len(attr_name)
                is_on_attr = attr_start <= target_offset <= attr_end
                if is_on_attr:
                    self._context.is_attribute = True
                    self._context.token_name = attr_name
                    raise ContextFoundException()
                attr_value_start = attr_end + 2  # +2 for '=' and '\"'
                attr_value_end = attr_value_start + len(attr_value)
                is_on_attr_value = attr_value_start <= target_offset <= attr_value_end
                if is_on_attr_value:
                    self._context.is_attribute_value = True
                    self._context.token_name = attr_value
                    raise ContextFoundException()
                accum = attr_end

    def endElement(self, tag):
        pass

    def characters(self, content):
        pass

    def get_current_position(self) -> Position:
        return Position(line=self._loc.getLineNumber() - 1, character=self._loc.getColumnNumber())


class MyErrorHandler(xml.sax.ErrorHandler):
    _context: XmlContext

    def __init__(self, context: XmlContext):
        xml.sax.ErrorHandler.__init__(self)
        self._context = context

    def error(self, exception: xml.sax.SAXParseException):
        pass

    def fatalError(self, exception: xml.sax.SAXParseException):
        position = self.get_position(exception)
        if exception.getMessage() == "unclosed token":
            self._try_process_context_from_unclosed_token(position)

    def warning(self, exception: xml.sax.SAXParseException):
        pass

    def get_position(self, exception: xml.sax.SAXParseException) -> Position:
        return Position(line=exception.getLineNumber() - 1, character=exception.getColumnNumber())

    def _try_process_context_from_unclosed_token(self, start_position: Position) -> None:
        # TODO search directly on context line
        # self._context.document_line
        pass


class ContextFoundException(Exception):
    """When raised, this exception indicates that the parsing can be stopped,
    since there is enought information for the context.
    """

    pass
