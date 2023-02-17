import pytest
from lsprotocol.types import Position

from galaxyls.tests.unit.utils import TestUtils


@pytest.mark.parametrize(
    "source_with_mark, expected_position",
    [
        ("^<root attr=></root>", Position(line=0, character=0)),
        ("<roo^t attr=></root>", Position(line=0, character=4)),
        ("<root>^\n</root>", Position(line=0, character=6)),
        ("<root>\n^</root>", Position(line=1, character=0)),
        ("<root>\n</root>^", Position(line=1, character=7)),
    ],
)
def test_extract_mark_from_source(
    source_with_mark: str,
    expected_position: Position,
) -> None:
    mark = "^"
    position, source = TestUtils.extract_mark_from_source(mark, source_with_mark)

    assert mark not in source
    assert position == expected_position
