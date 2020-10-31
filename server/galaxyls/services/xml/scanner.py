""" Based on the Lemminx implementation of the XML parser:
https://github.com/eclipse/lemminx/tree/master/org.eclipse.lemminx/src/main/java/org/eclipse/lemminx/dom/parser
"""

from typing import Optional
from .utils import MultiLineStream
from .types import ScannerState, TokenType
from .constants import (
    _RAN,
    _LAN,
    _EXL,
    _FSL,
    _EQS,
    _UDS,
    QUOTE_CHARS,
    CDATA_START_CHAR_SEQ,
    CDATA_END_CHAR_SEQ,
    COMMENT_START_CHAR_SEQ,
    COMMENT_END_CHAR_SEQ,
)

ERROR_UNEXPECTED_WHITESPACE = "Unexpected whitespace. Tag name must directly follow the open angle bracket."


class XmlScanner:
    def __init__(self, source: str, initial_offset: int = 0, initial_state: ScannerState = ScannerState.WithinContent) -> None:
        self.stream = MultiLineStream(source, initial_offset)
        self.state = initial_state
        self.token_offset = 0
        self.token_type = TokenType.Unknown
        self.token_error: Optional[str] = None

    def scan(self) -> TokenType:
        ofsset = self.stream.pos()
        token = self._internal_scan()
        if token != TokenType.EOS and ofsset == self.stream.pos():
            self.stream.advance(1)
            return self._finish_token(ofsset, TokenType.Unknown)
        return token

    def get_token_type(self) -> TokenType:
        return self.token_type

    def get_token_offset(self) -> int:
        return self.token_offset

    def get_token_lenth(self) -> int:
        return self.stream.pos() - self.token_offset

    def get_token_end(self) -> int:
        return self.stream.pos()

    def get_token_text(self) -> str:
        return self.stream.get_source()[self.token_offset : self.stream.pos()]

    def get_token_error(self) -> Optional[str]:
        return self.token_error

    def get_scanner_state(self) -> ScannerState:
        return self.state

    def _finish_token(self, offset: int, type: TokenType, error_message: Optional[str] = None) -> TokenType:
        self.token_type = type
        self.token_offset = offset
        self.token_error = error_message
        return type

    def _internal_scan(self) -> TokenType:
        offset = self.stream.pos()
        if self.stream.eos():
            return self._finish_token(offset, TokenType.EOS)

        if self.state == ScannerState.WithinComment:
            if self.stream.advance_if_chars(COMMENT_END_CHAR_SEQ):
                return self._finish_token(offset, TokenType.EndCommentTag)
            self.stream.advance_until_chars(COMMENT_END_CHAR_SEQ)
            return self._finish_token(offset, TokenType.Comment)

        if self.state == ScannerState.WithinContent:
            if self.stream.advance_if_char(_LAN):
                if not self.stream.eos() and self.stream.peek_char() == _EXL:
                    if self.stream.advance_if_chars(COMMENT_START_CHAR_SEQ):
                        self.state = ScannerState.WithinComment
                        return self._finish_token(offset, TokenType.StartCommentTag)
                    if self.stream.advance_if_chars(CDATA_START_CHAR_SEQ):
                        self.state = ScannerState.WithinCDATA
                        return self._finish_token(offset, TokenType.CDATATagOpen)
                if self.stream.advance_if_char(_FSL):
                    self.state = ScannerState.AfterOpeningEndTag
                    return self._finish_token(offset, TokenType.EndTagOpen)
                self.state = ScannerState.AfterOpeningStartTag
                return self._finish_token(offset, TokenType.StartTagOpen)
            self.stream.advance_until_char(_LAN)
            return self._finish_token(offset, TokenType.Content)

        if self.state == ScannerState.WithinCDATA:
            if self.stream.advance_if_chars(CDATA_END_CHAR_SEQ):
                self.state = ScannerState.WithinContent
                return self._finish_token(offset, TokenType.CDATATagClose)
            self.stream.advance_until_chars(CDATA_END_CHAR_SEQ)
            return self._finish_token(offset, TokenType.CDATAContent)

        if self.state == ScannerState.AfterOpeningEndTag:
            if self._has_next_element_name():
                self.state = ScannerState.WithinEndTag
                return self._finish_token(offset, TokenType.EndTag)
            if self.stream.skip_whitespace():
                return self._finish_token(
                    offset,
                    TokenType.Whitespace,
                    ERROR_UNEXPECTED_WHITESPACE,
                )
            self.state = ScannerState.WithinEndTag
            if self.stream.advance_until_char_or_new_tag(_RAN):
                if self.stream.peek_char() == _RAN:
                    self.state = ScannerState.WithinContent
                return self._internal_scan()
            return self._finish_token(offset, TokenType.Unknown)

        if self.state == ScannerState.WithinEndTag:
            if self.stream.skip_whitespace():
                return self._finish_token(offset, TokenType.Whitespace)
            if self.stream.advance_if_char(_RAN):
                self.state = ScannerState.WithinContent
                return self._finish_token(offset, TokenType.EndTagClose)
            if self.stream.advance_until_char(_LAN):
                self.state = ScannerState.WithinContent
                return self._internal_scan()
            return self._finish_token(offset, TokenType.Whitespace)

        if self.state == ScannerState.AfterOpeningStartTag:
            if self._has_next_element_name():
                self.state = ScannerState.WithinTag
                return self._finish_token(offset, TokenType.StartTag)
            if self.stream.skip_whitespace():
                return self._finish_token(
                    offset,
                    TokenType.Whitespace,
                    ERROR_UNEXPECTED_WHITESPACE,
                )
            self.state = ScannerState.WithinTag
            if self.stream.advance_until_char_or_new_tag(_RAN):
                if self.stream.peek_char() == _LAN:
                    self.state = ScannerState.WithinContent
                return self._internal_scan()
            return self._finish_token(offset, TokenType.Unknown)

        if self.state == ScannerState.WithinTag:
            if self.stream.skip_whitespace():
                return self._finish_token(offset, TokenType.Whitespace)
            if self._has_next_attribute_name():
                self.state = ScannerState.AfterAttributeName
                return self._finish_token(offset, TokenType.AttributeName)
            if self.stream.advance_if_char(_FSL):
                self.state = ScannerState.WithinTag
                if self.stream.advance_if_char(_RAN):
                    self.state = ScannerState.WithinContent
                    return self._finish_token(offset, TokenType.StartTagSelfClose)
                return self._finish_token(offset, TokenType.Unknown)
            ch = self.stream.peek_char()
            if ch in QUOTE_CHARS:
                self.state = ScannerState.BeforeAttributeValue
                return self._internal_scan()
            if self.stream.advance_if_char(_RAN):
                self.state = ScannerState.WithinContent
                return self._finish_token(offset, TokenType.StartTagClose)
            if self.stream.advance_until_char(_LAN):
                self.state = ScannerState.WithinContent
                return self._internal_scan()
            return self._finish_token(offset, TokenType.Unknown)

        if self.state == ScannerState.AfterAttributeName:
            if self.stream.skip_whitespace():
                return self._finish_token(offset, TokenType.Whitespace)
            if self.stream.advance_if_char(_EQS):
                self.state = ScannerState.BeforeAttributeValue
                return self._finish_token(offset, TokenType.DelimiterAssign)
            self.state = ScannerState.WithinTag
            return self._internal_scan()

        if self.state == ScannerState.BeforeAttributeValue:
            if self.stream.skip_whitespace():
                return self._finish_token(offset, TokenType.Whitespace)
            if self._has_next_attribute_value():
                self.state = ScannerState.WithinTag
                return self._finish_token(offset, TokenType.AttributeValue)
            self.state = ScannerState.WithinTag
            return self._internal_scan()

        self.stream.advance(1)
        self.state = ScannerState.WithinContent
        return self._finish_token(offset, TokenType.Unknown)

    def _has_next_element_name(self) -> bool:
        first = self.stream.peek_char()
        if not self._is_valid_start_name_character(str(first)):
            return False
        self.stream.advance(1)
        self.stream.advance_while_char(self._is_valid_name_character)
        return True

    def _has_next_attribute_name(self) -> bool:
        return self.stream.advance_while_char(self._is_valid_name_character) > 0

    def _has_next_attribute_value(self) -> bool:
        first = self.stream.peek_char()
        if first in QUOTE_CHARS:
            self.stream.advance(1)
            if self.stream.advance_until_char(first):
                self.stream.advance(1)
            return True
        return False

    def _is_valid_name_character(self, ch: str) -> bool:
        return ch.isalnum() or ch == _UDS

    def _is_valid_start_name_character(self, ch: str) -> bool:
        return ch.isalpha() or ch == _UDS  # No numbers allowed as first character
