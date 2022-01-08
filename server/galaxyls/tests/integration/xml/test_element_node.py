from typing import List, Tuple, cast
import pytest

from galaxyls.services.xml.nodes import XmlElement
from galaxyls.tests.unit.utils import TestUtils


class TestXmlElementClass:
    @pytest.mark.parametrize(
        "source, expected_offsets",
        [
            ("<test", (5, 5)),
            ("<test>", (5, 5)),
            ("<test ", (5, 5)),
            ('<test attr="val">', (6, 16)),
            ('<test attr="val"   attr2="value" >', (6, 32)),
        ],
    )
    def test_get_attributes_offsets_returns_expected(self, source: str, expected_offsets: Tuple[int, int]) -> None:
        xml_document = TestUtils.from_source_to_xml_document(source)
        node = xml_document.get_node_at(1)
        assert node
        assert node.is_element
        element = cast(XmlElement, node)

        actual_offsets = element.get_attributes_offsets()
        assert actual_offsets == expected_offsets

    @pytest.mark.parametrize(
        "source, expected_contents",
        [
            ('<test attr="val">', ['"val"']),
            ('<test attr="val"   attr2="value" >', ['"val"', '"value"']),
        ],
    )
    def test_get_attribute_content_returns_expected(self, source: str, expected_contents: List[str]) -> None:
        xml_document = TestUtils.from_source_to_xml_document(source)
        node = xml_document.get_node_at(1)
        assert node
        assert node.is_element
        element = cast(XmlElement, node)

        actual_contents = [attr.value.get_content(source) for attr in element.attributes.values() if attr.value is not None]
        assert actual_contents == expected_contents
