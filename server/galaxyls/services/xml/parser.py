""" This code is based on the Eclipse/Lemminx XML language server implementation:
https://github.com/eclipse/lemminx/tree/master/org.eclipse.lemminx/src/main/java/org/eclipse/lemminx/dom

Only the minimum subset of the XML dialect used by Galaxy tool wrappers is supported.
"""

from pygls.workspace import Document
from typing import Optional, cast
from .tokens import XmlAttribute, XmlCDATASection, XmlComment, XmlContent, XmlDocument, XmlElement, XmlSyntaxNode
from .types import TokenType
from .scanner import XmlScanner


class XmlDocumentParser:
    def parse(self, document: Document) -> XmlDocument:
        text = document.source
        scanner = XmlScanner(text)
        xml_document = XmlDocument(document)
        current: XmlSyntaxNode = xml_document
        attr: Optional[XmlAttribute] = None
        pending_attribute: Optional[str] = None
        last_closed = current
        end_tag_open_offset = -1
        tmp_white_space_content: Optional[XmlSyntaxNode] = None
        previous_token_was_end_tag_open = False
        token = scanner.scan()
        while token != TokenType.EOS:
            if tmp_white_space_content and token != TokenType.EndTagOpen:
                tmp_white_space_content = None

            if previous_token_was_end_tag_open:
                previous_token_was_end_tag_open = False
                if token != TokenType.EndTag:
                    # The expected token is not an EndTag, create a fake end tag element
                    self._create_fake_end_tag(end_tag_open_offset, current)

            if token == TokenType.StartTagOpen:
                if not current.is_closed and current.parent is not None:
                    # The next node's parent (current) is not closed at this point
                    # so the node's parent (current) will have its end position updated
                    current.end = scanner.get_token_offset()
                if current.is_closed:
                    # The next node being considered is a child of 'current' and if
                    # 'current' is already closed then 'current' was not updated properly.
                    current = cast(XmlSyntaxNode, current.parent)
                child = XmlElement(scanner.get_token_offset(), scanner.get_token_end())
                child.start_tag_open_offset = scanner.get_token_offset()
                child.parent = current
                current = child

            if token == TokenType.StartTag:
                element = cast(XmlElement, current)
                element.name = scanner.get_token_text()
                current.end = scanner.get_token_end()

            if token == TokenType.StartTagClose:
                if current.is_element:
                    current.end = scanner.get_token_end()
                    element = cast(XmlElement, current)
                    element.start_tag_close_offset = scanner.get_token_offset()
                if current.parent:
                    current._closed = True
                    current = current.parent
                current.end = scanner.get_token_end()

            if token == TokenType.EndTagOpen:
                if tmp_white_space_content is not None:
                    cast(XmlSyntaxNode, tmp_white_space_content).parent = current
                end_tag_open_offset = scanner.get_token_offset()
                current.end = scanner.get_token_offset()
                previous_token_was_end_tag_open = True

            if token == TokenType.EndTag:
                close_tag = scanner.get_token_text()
                node = current
                # eg: <a><b><c></d> will set a,b,c end position to the start of |</d>
                while (
                    not (current.is_element and cast(XmlElement, current).is_same_tag(close_tag))
                    and current.parent is not None
                ):
                    current.end = end_tag_open_offset
                    current = current.parent
                if current != xml_document:
                    current._closed = True
                    if current.is_element:
                        cast(XmlElement, current).end_tag_open_offset = end_tag_open_offset
                    current.end = scanner.get_token_end()
                else:
                    # element open tag not found (ex: <root>) add a fake element which only has an end tag (no start tag)
                    element = XmlElement(scanner.get_token_offset() - 2, scanner.get_token_end())
                    element.end_tag_open_offset = end_tag_open_offset
                    element.name = close_tag
                    element.parent = node
                    current = element

            if token == TokenType.StartTagSelfClose:
                if current.parent is not None:
                    current._closed = True
                    cast(XmlElement, current).is_self_closed = True
                    current.end = scanner.get_token_end()
                    last_closed = current
                    current = current.parent

            if token == TokenType.EndTagClose:
                if current.parent is not None:
                    current.end = scanner.get_token_end()
                    last_closed = current
                    if last_closed.is_element:
                        cast(XmlElement, last_closed).end_tag_close_offset = scanner.get_token_offset()
                    current = current.parent

            if token == TokenType.AttributeName:
                pending_attribute = scanner.get_token_text()
                element = cast(XmlElement, current)
                attr = XmlAttribute(
                    pending_attribute,
                    scanner.get_token_offset(),
                    scanner.get_token_offset() + len(pending_attribute),
                    element,
                )
                element.attributes[pending_attribute] = attr
                current.end = scanner.get_token_end()

            if token == TokenType.DelimiterAssign:
                if attr is not None:
                    # Sets the value to the '=' position in case there is no AttributeValue
                    attr.set_value(None, scanner.get_token_offset(), scanner.get_token_end())
                    attr.has_delimiter = True

            if token == TokenType.AttributeValue:
                value = scanner.get_token_text()
                if current.has_attributes and attr is not None:
                    attr.set_value(value, scanner.get_token_offset(), scanner.get_token_offset() + len(value))
                pending_attribute = None
                attr = None
                current.end = scanner.get_token_end()

            if token == TokenType.CDATATagOpen:
                cdata = XmlCDATASection(scanner.get_token_offset(), len(text))
                cdata.parent = current
                current = cdata

            if token == TokenType.CDATAContent:
                cdata = cast(XmlCDATASection, current)
                cdata.start_content = scanner.get_token_offset()
                cdata.end_content = scanner.get_token_end()
                current.end = scanner.get_token_end()

            if token == TokenType.CDATATagClose:
                current.end = scanner.get_token_end()
                current._closed = True
                current = cast(XmlSyntaxNode, current.parent)

            if token == TokenType.StartCommentTag:
                # In case the tag before the comment tag (current) was not properly
                # closed, current should be set to the root node
                if current.is_closed:
                    current = cast(XmlSyntaxNode, current.parent)
                comment = XmlComment(scanner.get_token_offset(), len(text))
                comment.parent = current
                current = comment

            if token == TokenType.Comment:
                comment = cast(XmlComment, current)
                comment.start_content = scanner.get_token_offset()
                comment.end_content = scanner.get_token_end()

            if token == TokenType.EndCommentTag:
                current.end = scanner.get_token_end()
                current._closed = True
                current = cast(XmlSyntaxNode, current.parent)

            if token == TokenType.Content:
                content = XmlContent(scanner.get_token_offset(), scanner.get_token_end())
                content._closed = True
                content.parent = current

        if previous_token_was_end_tag_open:
            previous_token_was_end_tag_open = False
            if token != TokenType.EndTag:
                # The expected token is not an EndTag, create a fake end tag element
                self._create_fake_end_tag(end_tag_open_offset, current)

        while current.parent is not None:
            current.end = len(text)
            current = current.parent

        return xml_document

    def _create_fake_end_tag(self, end_tag_open_offset, current):
        # The expected token is not an EndTag, create a fake end tag element
        element = XmlElement(end_tag_open_offset, end_tag_open_offset + 2)
        element.end_tag_open_offset = end_tag_open_offset
        element.parent = current
