NEW_LINE = "\n"

_EXL = ord("!")
_MIN = ord("-")
_UDS = ord("_")
_LAN = ord("<")
_RAN = ord(">")
_FSL = ord("/")
_EQS = ord("=")
_DQO = ord('"')
_SQO = ord("'")
_NWL = ord(NEW_LINE)
_CAR = ord("\r")
_LFD = ord("\f")
_WSP = ord(" ")
_TAB = ord("\t")
_OSB = ord("[")
_CSB = ord("]")
_CVL = ord("C")
_DVL = ord("D")
_AVL = ord("A")
_TVL = ord("T")
_QMA = ord("?")

WHITESPACE_CHARS = [_WSP, _TAB, _NWL, _LFD, _CAR]
QUOTE_CHARS = [_DQO, _SQO]
COMMENT_END_CHAR_SEQ = [_MIN, _MIN, _RAN]
COMMENT_START_CHAR_SEQ = [_EXL, _MIN, _MIN]
CDATA_START_CHAR_SEQ = [_EXL, _OSB, _CVL, _DVL, _AVL, _TVL, _AVL, _OSB]
CDATA_END_CHAR_SEQ = [_CSB, _CSB, _RAN]
PI_END_CHAR_SEQ = [_QMA, _RAN]

UNDEFINED_OFFSET = -1
