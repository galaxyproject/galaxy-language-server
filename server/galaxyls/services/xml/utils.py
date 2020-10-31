import re
from typing import List
from .constants import WHITESPACE_CHARS


class MultiLineStream:
    def __init__(self, source: str, position: int = 0) -> None:
        self._source = source
        self._position = position
        self._len = len(source)

    def eos(self) -> bool:
        return self._len <= self._position

    def get_source(self) -> str:
        return self._source

    def pos(self) -> int:
        return self._position

    def go_back_to(self, pos: int) -> None:
        self._position = pos

    def go_back(self, n: int) -> None:
        self._position -= n

    def advance(self, n: int) -> None:
        self._position = self._position + n

    def go_to_end(self) -> None:
        self._position = self._len

    def next_char(self) -> int:
        try:
            self._position = self._position + 1
            return ord(self._source[self._position])
        except IndexError:
            return 0

    def peek_char(self, n: int = 0) -> int:
        try:
            return ord(self._source[self._position + n])
        except IndexError:
            return 0

    def advance_if_char(self, ch: int) -> bool:
        if ch == self._source[self._position]:
            self._position = self._position + 1
            return True
        return False

    def advance_if_chars(self, ch: List[int]) -> bool:
        if self._position + len(ch) > self._len:
            return False
        i = 0
        for i in range(len(ch)):
            if self._source[self._position + i] != ch[i]:
                return False
        self.advance(i)
        return True

    def advance_if_regex(self, regex: str) -> str:
        string = self._source[self._position :]
        match = re.match(regex, string)
        if match:
            self._position = self._position + match.end(0)
            return match[0]
        return ""

    def advance_until_regex(self, regex: str) -> str:
        string = self._source[self._position :]
        match = re.match(regex, string)
        if match:
            self._position = self._position + match.start(0)
            return match[0]
        else:
            self.go_to_end()
        return ""

    def advance_until_char(self, ch: int) -> bool:
        while self._position < self._len:
            if self._source[self._position] == ch:
                return True
            self.advance(1)
        return False

    def advance_until_chars(self, ch: List[int]) -> bool:
        while self._position + len(ch) <= self._len:
            i = 0
            for i in range(len(ch)):
                if self._source[self._position + i] == ch[i]:
                    continue
            if i == len(ch):
                return True
            self.advance(i)
        self.go_to_end()
        return False

    def advance_while_char_in(self, list: List[int]) -> int:
        pos_now = self._position
        while self._position < self._len and ord(self._source[self._position]) in list:
            self._position = self._position + 1
        return self._position - pos_now

    def skip_whitespace(self) -> bool:
        n = self.advance_while_char_in(WHITESPACE_CHARS)
        return n > 0
