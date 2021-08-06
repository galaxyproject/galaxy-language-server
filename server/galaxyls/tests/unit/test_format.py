from ...services.format import GalaxyToolFormatService
from pygls.lsp.types import (
    DocumentFormattingParams,
    TextDocumentIdentifier,
    FormattingOptions,
)

FAKE_INVALID_DOCUMENT = """
<invalid> XML content
"""

FAKE_UNFORMATTED_DOCUMENT = """
<tool id="1">   <test><![CDATA[This is a test.]]></test> </tool>
"""

EXPECTED_FORMATTED_DOCUMENT = """<tool id="1">
    <test><![CDATA[This is a test.]]></test>
</tool>
"""


class TestGalaxyToolFormatServiceClass:
    def test_format_should_return_whole_file_text_edit(self):
        service = GalaxyToolFormatService()
        params = DocumentFormattingParams(
            text_document=TextDocumentIdentifier(uri="test"),
            options=FormattingOptions(tab_size=4, insert_spaces=True),
        )

        actual = service.format(FAKE_UNFORMATTED_DOCUMENT, params)

        assert len(actual) == 1
        assert actual[0].range.start.line == 0
        assert actual[0].range.start.character == 0
        assert actual[0].range.end.line == 3
        assert actual[0].range.end.character == 0

    def test_format_document_returns_expected_format(self):
        service = GalaxyToolFormatService()

        actual = service.format_content(FAKE_UNFORMATTED_DOCUMENT, tabSize=4)

        assert actual == EXPECTED_FORMATTED_DOCUMENT

    def test_format_document_maintains_cdata(self):
        service = GalaxyToolFormatService()

        actual = service.format_content(FAKE_UNFORMATTED_DOCUMENT, tabSize=4)

        assert "<![CDATA[This is a test.]]>" in actual

    def test_format_document_do_not_change_invalid_xml(self):
        service = GalaxyToolFormatService()

        actual = service.format_content(FAKE_INVALID_DOCUMENT, tabSize=4)

        assert actual == FAKE_INVALID_DOCUMENT
