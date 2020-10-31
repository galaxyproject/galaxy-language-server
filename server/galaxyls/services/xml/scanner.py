""" Based on the Lemminx implementation of the XML parser:
https://github.com/eclipse/lemminx/tree/master/org.eclipse.lemminx/src/main/java/org/eclipse/lemminx/dom/parser
"""

from .utils import MultiLineStream
from .types import ScannerState, TokenType
from typing import Optional


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
        raise NotImplementedError
