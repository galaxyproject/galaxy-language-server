from enum import Enum, unique


@unique
class TokenType(Enum):

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
