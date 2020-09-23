"""This module provides a service to determine position context inside an XML document."""

from typing import Optional, List
from io import BytesIO
from pygls.workspace import Document, Position
from pygls.types import Range
from enum import Enum, unique
import xml.sax
import re
from .xsd.types import XsdTree, XsdNode


CDATA_BLOCK_START_SIZE = len("<![CDATA[")
CDATA_BLOCK_END_SIZE = len("]]>")
START_TAG_REGEX = r"<([a-z_]+)[ \n\W]?"
ATTR_KEY_VALUE_REGEX = r" ([a-z_]*)=\"([\w. ]*)[\"]?"
TAG_GROUP = 1
ATTR_KEY_GROUP = 1
ATTR_VALUE_GROUP = 2
SUPPORTED_RECOVERY_EXCEPTIONS = [
    "unclosed token",
    "no element found",
    "not well-formed (invalid token)",
]


@unique
class ContextTokenType(Enum):
    """Supported types of tokens that can be found in a document."""

    UNKNOWN = 1
    TAG = 2
    ATTRIBUTE_KEY = 3
    ATTRIBUTE_VALUE = 4


class XmlContext:
    """Represents the context at a given XML document position.

    It provides information about the token under the cursor and
    the XSD node definition associated.
    """

    def __init__(
        self,
        document_line: str = "",
        position: Position = Position(),
        is_empty: bool = False,
        token_name: str = None,
        token_type: ContextTokenType = ContextTokenType.UNKNOWN,
    ):
        self.document_line = document_line
        self.target_position = position
        self.is_empty = is_empty
        self.token_name = token_name
        self.token_type = token_type
        self.token_range: Range = None
        self.attr_name = None
        self.node: Optional[XsdNode] = None
        self.is_node_content: bool = False
        self.node_stack: List[str] = []
        self.is_invalid: bool = False

    def is_tag(self) -> bool:
        """Indicates if the token in context is a tag"""
        return self.token_type == ContextTokenType.TAG

    def is_attribute_key(self) -> bool:
        """Indicates if the token in context is an attribute key"""
        return self.token_type == ContextTokenType.ATTRIBUTE_KEY

    def is_attribute_value(self) -> bool:
        """Indicates if the token in context is an attribute value"""
        return self.token_type == ContextTokenType.ATTRIBUTE_VALUE

    def update_node_definition(self, xsd_tree: XsdTree) -> None:
        """Updates the associated node in the context using the given XSD tree definition.

        Args:
            xsd_tree (XsdTree): The XSD tree definition.
        """
        self.node = xsd_tree.find_node_by_stack(self.node_stack)
        if not self.node:
            self.node = xsd_tree.root


class XmlContextService:
    """This service provides information about the XML context at
    a specific position of the document.
    """

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
        parser = XmlContextParser()
        context = parser.parse(document, position)
        context.update_node_definition(self.xsd_tree)
        return context


class XmlContextParser:
    """This class parses an XML document until it finds the token at a given
    position (line and character) and returns information about it.

    The parser will try it's best to be tolerant to imcomplete XML documents
    in order to be able to extract the token at position.
    """

    def __init__(self):
        self._document: Document = None

    def parse(self, document: Document, position: Position) -> XmlContext:
        """Parses the given document until it finds the token at the given position and
        returns context information about this token.

        Args:
            document (Document): The XML document to parse.
            position (Position): The position inside the document to get the context.

        Returns:
            XmlContext: The context information at the given position.
        """
        self._document = document

        if self.is_empty_document(document):
            return XmlContext(is_empty=True)

        context_line = document.lines[position.line]
        context = XmlContext(document_line=context_line, position=position)

        source = BytesIO(document.source.encode())
        reader = self._build_xml_reader(context)

        try:
            reader.parse(source)
        except ContextFoundException:
            pass  # All is good, we got what we needed

        return context

    def _build_xml_reader(self, context: XmlContext) -> xml.sax.xmlreader.XMLReader:
        reader = xml.sax.make_parser()
        reader.setFeature(xml.sax.handler.feature_namespaces, False)
        reader.setFeature(xml.sax.handler.feature_validation, False)
        locator = xml.sax.expatreader.ExpatLocator(reader)
        saxhandler = ContextBuilderHandler(locator, context)
        reader.setProperty(xml.sax.handler.property_lexical_handler, saxhandler)
        reader.setContentHandler(saxhandler)
        reader.setErrorHandler(ContextParseErrorHandler(context))
        return reader

    @staticmethod
    def is_empty_document(document: Document) -> bool:
        """Determines if the given XML document is an empty document.

        Args:
            document (Document): The document to check.

        Returns:
            bool: True if the document is empty and False otherwise.
        """
        xml_content = document.source.strip()
        return not xml_content or len(xml_content) < 2


class ContextBuilderHandler(xml.sax.ContentHandler):
    """SAX ContentHandler that tries to compose the context information using the
    different SAX events.
    """

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
        self._context.node_stack.append(tag)
        current_position = self.get_current_position()
        if current_position.line == self._context.target_position.line:
            self._build_context_from_element_line(current_position.character, tag, attributes)

    def endElement(self, tag):
        current_position = self.get_current_position()
        if current_position.line < self._context.target_position.line:
            self._context.node_stack.pop(-1)
        elif current_position.line == self._context.target_position.line:
            line_after_position = self._context.document_line[current_position.character :]
            closing_tag = f"</{tag}>"
            is_fully_closed = line_after_position.find(closing_tag) >= 0
            tag_start = current_position.character
            tag_end = current_position.character + len(closing_tag)
            if is_fully_closed and tag_start <= self._context.target_position.character <= tag_end:
                self._context.token_type = ContextTokenType.TAG
                self._context.token_name = tag
                self._context.token_range = Range(
                    Position(line=current_position.line, character=tag_start),
                    Position(line=current_position.line, character=tag_end),
                )
                raise ContextFoundException()
            if (
                is_fully_closed
                and self._context.target_position.character > tag_end
                or not is_fully_closed
                and self._context.target_position.character >= current_position.character
            ):
                self._context.node_stack.pop(-1)

    def characters(self, content):
        if self._is_target_at_current_element(len(content)):
            self._context.is_node_content = True
            raise ContextFoundException()

    def comment(self, content):
        pass

    def startDTD(self, name, public_id, system_id):
        pass

    def endDTD(self):
        pass

    def startEntity(self, name):
        pass

    def endEntity(self, name):
        pass

    def startCDATA(self):
        if self._is_target_at_current_element(CDATA_BLOCK_START_SIZE):
            self._context.is_node_content = True
            raise ContextFoundException()

    def endCDATA(self):
        if self._is_target_at_current_element(CDATA_BLOCK_END_SIZE):
            self._context.is_node_content = True
            raise ContextFoundException()

    def get_current_position(self) -> Position:
        """Gets the current position inside the document where the parser is.

        Returns:
            Position: The current position inside the document.
        """
        return Position(line=self._loc.getLineNumber() - 1, character=self._loc.getColumnNumber())

    def _is_target_at_current_element(self, element_size: int) -> bool:
        current_position = self.get_current_position()
        if current_position.line == self._context.target_position.line:
            element_start = current_position.character
            content_end = current_position.character + element_size
            return element_start <= self._context.target_position.character <= content_end
        return False

    def _build_context_from_element_line(self, start_position: int, tag: str, attributes):
        target_offset = self._context.target_position.character
        tag_offset = start_position + len(tag)
        is_on_tag = start_position <= target_offset <= tag_offset
        if is_on_tag:
            self._context.token_type = ContextTokenType.TAG
            self._context.token_name = tag
            self._context.token_range = Range(
                Position(line=self._context.target_position.line, character=start_position + 1),
                Position(line=self._context.target_position.line, character=tag_offset + 1),
            )
            raise ContextFoundException()

        accum = tag_offset + 1  # +1 for '<'
        for attr_name, attr_value in attributes.items():
            attr_start = accum + 1  # +1 for ' '
            attr_end = attr_start + len(attr_name)
            is_on_attr = attr_start <= target_offset <= attr_end
            if is_on_attr:
                self._context.token_type = ContextTokenType.ATTRIBUTE_KEY
                self._context.token_name = attr_name
                self._context.token_range = Range(
                    Position(line=self._context.target_position.line, character=attr_start),
                    Position(line=self._context.target_position.line, character=attr_end),
                )
                raise ContextFoundException()

            attr_value_start = attr_end + 2  # +2 for '=' and '\"'
            attr_value_end = attr_value_start + len(attr_value)
            is_on_attr_value = attr_value_start <= target_offset <= attr_value_end
            if is_on_attr_value:
                self._context.token_type = ContextTokenType.ATTRIBUTE_VALUE
                self._context.token_name = attr_value
                self._context.attr_name = attr_name
                self._context.token_range = Range(
                    Position(line=self._context.target_position.line, character=attr_value_start),
                    Position(line=self._context.target_position.line, character=attr_value_end),
                )
                raise ContextFoundException()
            accum = attr_value_end + 1  # closing \"


class ContextParseErrorHandler(xml.sax.ErrorHandler):
    """SAX ErrorHandler that tries it's best to recover context information when a fatal error
    ocurred during parsing.
    """

    def __init__(self, context: XmlContext):
        xml.sax.ErrorHandler.__init__(self)
        self._context = context

    def fatalError(self, exception: xml.sax.SAXParseException):
        position = self.get_position(exception)
        if exception.getMessage() in SUPPORTED_RECOVERY_EXCEPTIONS:
            self._try_recover_context_from_exception(position.character)
        else:
            self._context.is_invalid = True

    def get_position(self, exception: xml.sax.SAXParseException) -> Position:
        return Position(line=exception.getLineNumber() - 1, character=exception.getColumnNumber())

    def _try_recover_context_from_exception(self, start_offset: int) -> None:
        target_offset = self._context.target_position.character
        self._try_get_tag_context_at_line_position(target_offset)
        self._try_get_attribute_context_at_line_position(target_offset)

    def _try_get_tag_context_at_line_position(self, target_offset):
        tag_matches = re.finditer(START_TAG_REGEX, self._context.document_line, re.DOTALL)
        if tag_matches:
            for match in tag_matches:
                tag = match.group(TAG_GROUP)
                tag_start = match.start(TAG_GROUP)
                tag_end = match.end(TAG_GROUP)
                if tag_start <= target_offset <= tag_end:
                    self._context.token_type = ContextTokenType.TAG
                    self._context.token_name = tag
                    self._context.token_range = Range(
                        Position(line=self._context.target_position.line, character=tag_start),
                        Position(line=self._context.target_position.line, character=tag_end),
                    )
                    if tag not in self._context.node_stack:
                        self._context.node_stack.append(tag)
                    raise ContextFoundException()

                if (
                    target_offset > tag_end
                    and tag not in self._context.node_stack
                    and not self._is_tag_closed_before_offset(tag, target_offset)
                ):
                    self._context.node_stack.append(tag)

    def _is_tag_closed_before_offset(self, tag: str, offset: int) -> bool:
        match_close = re.search(f"</{tag}>", self._context.document_line)
        if match_close and offset >= match_close.end(0):
            return True
        match_self_close = re.search(f"<{tag}[^>]*/>", self._context.document_line)
        return match_self_close and offset >= match_self_close.end(0)

    def _try_get_attribute_context_at_line_position(self, target_offset):
        attribute_matches = re.finditer(
            ATTR_KEY_VALUE_REGEX, self._context.document_line, re.DOTALL
        )
        if attribute_matches:
            for match in attribute_matches:
                if match.start(ATTR_KEY_GROUP) <= target_offset <= match.end(ATTR_KEY_GROUP):
                    self._context.token_type = ContextTokenType.ATTRIBUTE_KEY
                    self._context.token_name = match.group(ATTR_KEY_GROUP)
                    self._context.token_range = Range(
                        Position(
                            line=self._context.target_position.line,
                            character=match.start(ATTR_KEY_GROUP),
                        ),
                        Position(
                            line=self._context.target_position.line,
                            character=match.end(ATTR_KEY_GROUP),
                        ),
                    )
                    raise ContextFoundException()
                if match.start(ATTR_VALUE_GROUP) <= target_offset <= match.end(ATTR_VALUE_GROUP):
                    self._context.token_type = ContextTokenType.ATTRIBUTE_VALUE
                    self._context.token_name = match.group(ATTR_VALUE_GROUP)
                    self._context.attr_name = match.group(ATTR_KEY_GROUP)
                    self._context.token_range = Range(
                        Position(
                            line=self._context.target_position.line,
                            character=match.start(ATTR_VALUE_GROUP),
                        ),
                        Position(
                            line=self._context.target_position.line,
                            character=match.end(ATTR_VALUE_GROUP),
                        ),
                    )
                    raise ContextFoundException()


class ContextFoundException(Exception):
    """When this exception is raised, it indicates that the necessary
    information for the context is already retrieved, so, additional
    parsing of the file can be avoided.
    """

    pass
