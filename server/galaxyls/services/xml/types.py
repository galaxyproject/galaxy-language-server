from enum import Enum, unique


@unique
class DocumentType(Enum):
    """Supported types of XML documents."""

    UNKNOWN = 1
    TOOL = 2
    MACROS = 3


@unique
class NodeType(Enum):
    """Supported types of document nodes."""

    UNKNOWN = 1
    ELEMENT = 2
    ATTRIBUTE = 3
    ATTRIBUTE_KEY = 4
    ATTRIBUTE_VALUE = 5
    CDATA_SECTION = 6
    COMMENT = 7
    CONTENT = 8
    PROCESSING_INSTRUCTION = 9
    DOCUMENT = 10


@unique
class TokenType(Enum):
    """Types of tokens in a XML document."""

    StartCommentTag = 1
    Comment = 2
    EndCommentTag = 3
    CDATATagOpen = 4
    CDATAContent = 5
    CDATATagClose = 6
    StartTagOpen = 7
    StartTagClose = 8
    StartTagSelfClose = 9
    StartTag = 10
    EndTagOpen = 11
    EndTagClose = 12
    EndTag = 13
    DelimiterAssign = 14
    AttributeName = 15
    AttributeValue = 16
    StartPrologOrPI = 17
    PrologName = 18
    PIName = 19
    PIContent = 20
    PIEnd = 21
    PrologEnd = 22
    Content = 23
    Whitespace = 24
    Unknown = 25
    EOS = 26


@unique
class ScannerState(Enum):
    """Possible states of the XML scanner."""

    WithinContent = 1
    AfterOpeningStartTag = 2
    AfterOpeningEndTag = 3
    WithinTag = 4
    WithinEndTag = 5
    WithinComment = 6
    AfterAttributeName = 7
    BeforeAttributeValue = 8
    WithinCDATA = 9
    AfterClosingCDATATag = 10
    StartCDATATag = 11
    AfterPrologOpen = 12
    PrologOrPI = 13
    WithinPI = 14
