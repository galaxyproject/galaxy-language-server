import pytest
from galaxyls.services.xml.utils import convert_document_offset_to_position, convert_document_offsets_to_range
from galaxyls.tests.unit.utils import TestUtils
from pygls.lsp.types import Position, Range


class TestXmlUtils:
    @pytest.mark.parametrize(
        "source, offset, expected_position",
        [
            ("<tool></tool>", 0, Position(line=0, character=0)),
            ("<tool></tool>", 13, Position(line=0, character=13)),
            ("<tool></tool>\n", 14, Position(line=1, character=0)),
            ("<tool>\n<description/>\n<inputs>\n</tool>", 6, Position(line=0, character=6)),
            ("<tool>\n<description/>\n<inputs>\n</tool>", 7, Position(line=1, character=0)),
            ("<tool>\n<description/>\n<inputs>\n</tool>", 21, Position(line=1, character=14)),
            ("<tool>\n<description/>\n<inputs>\n</tool>", 22, Position(line=2, character=0)),
            ("<tool>\n<description/>\n<inputs>\n</tool>", 30, Position(line=2, character=8)),
            ("<tool>\n<description/>\n<inputs>\n</tool>", 38, Position(line=3, character=7)),
        ],
    )
    def test_convert_document_offset_to_position_returns_expected_result(
        self, source: str, offset: int, expected_position: Position
    ) -> None:
        document = TestUtils.to_document(source)

        actual_position = convert_document_offset_to_position(document, offset)

        assert actual_position == expected_position

    @pytest.mark.parametrize(
        "source, start_offset, end_offset, expected_range",
        [
            (
                "<tool></tool>",
                0,
                6,
                Range(start=Position(line=0, character=0), end=Position(line=0, character=6)),
            ),
            (
                "<tool>\n</tool>",
                0,
                14,
                Range(start=Position(line=0, character=0), end=Position(line=1, character=7)),
            ),
            (
                "<tool>\n<description/>\n</tool>",
                7,
                21,
                Range(start=Position(line=1, character=0), end=Position(line=1, character=14)),
            ),
            (
                "<tool>\n<description/>\n</tool>\n",
                0,
                30,
                Range(start=Position(line=0, character=0), end=Position(line=3, character=0)),
            ),
        ],
    )
    def test_convert_document_offsets_to_range_returns_expected_result(
        self, source: str, start_offset: int, end_offset: int, expected_range: Range
    ) -> None:
        document = TestUtils.to_document(source)

        actual_range = convert_document_offsets_to_range(document, start_offset, end_offset)

        assert actual_range == expected_range
