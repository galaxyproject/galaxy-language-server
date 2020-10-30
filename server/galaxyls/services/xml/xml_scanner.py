""" Based on the Lemminx implementation of the XML parser:
https://github.com/eclipse/lemminx/tree/master/org.eclipse.lemminx/src/main/java/org/eclipse/lemminx/dom/parser
"""

import re
from .types import ScannerState, TokenType
from typing import List, Optional

_BNG = ord("!")
_MIN = ord("-")
_LAN = ord("<")
_RAN = ord(">")
_FSL = ord("/")
_EQS = ord("=")
_DQO = ord('"')
_SQO = ord("'")
_NWL = ord("\n")
_CAR = ord("\r")
_LFD = ord("\f")
_WSP = ord(" ")
_TAB = ord("\t")


class Scanner:
    def scan(self) -> TokenType:
        raise NotImplementedError

    def get_token_type(self) -> TokenType:
        raise NotImplementedError

    def get_token_offset(self) -> int:
        raise NotImplementedError

    def get_token_lenth(self) -> int:
        raise NotImplementedError

    def get_token_end(self) -> int:
        raise NotImplementedError

    def get_token_text(self) -> str:
        raise NotImplementedError

    def get_token_error(self) -> Optional[str]:
        raise NotImplementedError

    def get_scanner_state(self) -> ScannerState:
        raise NotImplementedError


class MultiLineStream:
    def __init__(self, source: str, position: int = 0) -> None:
        self.__source = source
        self.__position = position
        self.__len = len(source)

    def eos(self) -> bool:
        return self.__len <= self.__position

    def get_source(self) -> str:
        return self.__source

    def pos(self) -> int:
        return self.__position

    def go_back_to(self, pos: int) -> None:
        self.__position = pos

    def go_back(self, n: int) -> None:
        self.__position -= n

    def advance(self, n: int) -> None:
        self.__position = self.__position + n

    def go_to_end(self) -> None:
        self.__position = self.__len

    def next_char(self) -> int:
        try:
            self.__position = self.__position + 1
            return ord(self.__source[self.__position])
        except IndexError:
            return 0

    def peek_char(self, n: int = 0) -> int:
        try:
            return ord(self.__source[self.__position + n])
        except IndexError:
            return 0

    def advance_if_char(self, ch: int) -> bool:
        if ch == self.__source[self.__position]:
            self.__position = self.__position + 1
            return True
        return False

    def advance_if_chars(self, ch: List[int]) -> bool:
        if self.__position + len(ch) > self.__len:
            return False
        i = 0
        for i in range(len(ch)):
            if self.__source[self.__position + i] != ch[i]:
                return False
        self.advance(i)
        return True

    def advance_if_regex(self, regex: str) -> str:
        string = self.__source[self.__position :]
        match = re.match(regex, string)
        if match:
            self.__position = self.__position + match.end(0)
            return match[0]
        return ""

    def advance_until_regex(self, regex: str) -> str:
        string = self.__source[self.__position :]
        match = re.match(regex, string)
        if match:
            self.__position = self.__position + match.start(0)
            return match[0]
        else:
            self.go_to_end()
        return ""

    def advance_until_char(self, ch: int) -> bool:
        while self.__position < self.__len:
            if self.__source[self.__position] == ch:
                return True
            self.advance(1)
        return False

    def advance_until_chars(self, ch: List[int]) -> bool:
        while self.__position + len(ch) <= self.__len:
            i = 0
            for i in range(len(ch)):
                if self.__source[self.__position + i] == ch[i]:
                    continue
            if i == len(ch):
                return True
            self.advance(i)
        self.go_to_end()
        return False

    def advance_while_char_in(self, list: List[int]) -> int:
        pos_now = self.__position
        while self.__position < self.__len and ord(self.__source[self.__position]) in list:
            self.__position = self.__position + 1
        return self.__position - pos_now

    def skip_whitespace(self) -> bool:
        n = self.advance_while_char_in([_WSP, _TAB, _NWL, _LFD, _CAR])
        return n > 0


class XmlScanner(Scanner):
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
