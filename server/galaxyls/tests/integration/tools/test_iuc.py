from typing import cast

import pytest
from galaxyls.services.tools.iuc import IUCToolParamAttributeSorter
from galaxyls.services.xml.nodes import XmlElement
from galaxyls.tests.unit.utils import TestUtils
from pygls.types import Position, Range


class TestIUCToolParamAttributeSorterClass:
    def test_sort_param__without_attributes_returns_none(self) -> None:
        xml_document = TestUtils.from_source_to_xml_document("<test>")
        node = xml_document.get_node_at(1)
        assert node.is_element
        element = cast(XmlElement, node)

        sorter = IUCToolParamAttributeSorter()

        actual = sorter.sort_param_attributes(element, xml_document)

        assert actual is None

    @pytest.mark.parametrize(
        "source, expected_range, expected_text",
        [
            (
                "<test format=",
                Range(Position(0, 6), Position(0, 13)),
                'format=""',
            ),
            (
                '<test format="val1">',
                Range(Position(0, 6), Position(0, 19)),
                'format="val1"',
            ),
            (
                '<test format="val1"   type="val2" >',
                Range(Position(0, 6), Position(0, 33)),
                'type="val2" format="val1"',
            ),
            (
                '<test format="val1" name="val2" type="val3">',
                Range(Position(0, 6), Position(0, 43)),
                'name="val2" type="val3" format="val1"',
            ),
            (
                '<test unknown="val0" format="val1" name="val2" type="val3">',
                Range(Position(0, 6), Position(0, 58)),
                'name="val2" type="val3" format="val1" unknown="val0"',
            ),
        ],
    )
    def test_sort_param_attributes_returns_expected_range_and_text(
        self,
        source: str,
        expected_range: Range,
        expected_text: str,
    ) -> None:
        xml_document = TestUtils.from_source_to_xml_document(source)
        node = xml_document.get_node_at(1)
        assert node.is_element
        element = cast(XmlElement, node)

        sorter = IUCToolParamAttributeSorter()

        actual = sorter.sort_param_attributes(element, xml_document)

        assert actual
        assert actual.replace_range == expected_range
        assert actual.text == expected_text

    @pytest.mark.parametrize(
        "source, expected_edits_count",
        [
            ("", 0),
            ("<test>", 0),
            ("<test><param/></test>", 0),
            ("<test><param></param></test>", 0),
            ('<test><param name="val"></param></test>', 1),
            (
                """
                <test>
                    <param />
                    <param name="val"/>
                </test>
                """,
                1,
            ),
            (
                """
                <test>
                    <param name="val"/>
                    <param name="val"/>
                    <param name="val"/>
                </test>
                """,
                3,
            ),
        ],
    )
    def test_sort_document_param_attributes_returns_expected_result_count(
        self,
        source: str,
        expected_edits_count: int,
    ) -> None:
        xml_document = TestUtils.from_source_to_xml_document(source)
        sorter = IUCToolParamAttributeSorter()

        actual = sorter.sort_document_param_attributes(xml_document)

        assert len(actual) == expected_edits_count
