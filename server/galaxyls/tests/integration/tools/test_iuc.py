from typing import cast

import pytest
from galaxyls.services.tools.iuc import IUCToolParamAttributeSorter
from galaxyls.services.xml.nodes import XmlElement
from galaxyls.tests.unit.utils import TestUtils
from pygls.lsp.types import Position, Range


class TestIUCToolParamAttributeSorterClass:
    def test_sort_param_without_attributes_returns_none(self) -> None:
        xml_document = TestUtils.from_source_to_xml_document("<param>")
        node = xml_document.get_node_at(1)
        assert node
        assert node.is_element
        element = cast(XmlElement, node)

        sorter = IUCToolParamAttributeSorter()

        actual = sorter.sort_param_attributes(element, xml_document)

        assert actual is None

    def test_sort_param_with_single_attribute_returns_none(self) -> None:
        xml_document = TestUtils.from_source_to_xml_document('<param format="val1">')
        node = xml_document.get_node_at(1)
        assert node
        assert node.is_element
        element = cast(XmlElement, node)

        sorter = IUCToolParamAttributeSorter()

        actual = sorter.sort_param_attributes(element, xml_document)

        assert actual is None

    def test_sort_param_with_sorted_attributes_returns_none(self) -> None:
        xml_document = TestUtils.from_source_to_xml_document('<param name="n" format="f">')
        node = xml_document.get_node_at(1)
        assert node
        assert node.is_element
        element = cast(XmlElement, node)

        sorter = IUCToolParamAttributeSorter()

        actual = sorter.sort_param_attributes(element, xml_document)

        assert actual is None

    @pytest.mark.parametrize(
        "source, expected_range, expected_text",
        [
            (
                '<param format="val1" name="n">',
                Range(
                    start=Position(line=0, character=7),
                    end=Position(line=0, character=29),
                ),
                'name="n" format="val1"',
            ),
            (
                '<param format="val1"   type="val2" >',
                Range(
                    start=Position(line=0, character=7),
                    end=Position(line=0, character=34),
                ),
                'type="val2" format="val1"',
            ),
            (
                '<param format="val1" name="val2" type="val3">',
                Range(
                    start=Position(line=0, character=7),
                    end=Position(line=0, character=44),
                ),
                'name="val2" type="val3" format="val1"',
            ),
            (
                '<param unknown="val0" format="val1" name="val2" type="val3">',
                Range(
                    start=Position(line=0, character=7),
                    end=Position(line=0, character=59),
                ),
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
        assert node
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
            ('<test><param name="val"></param></test>', 0),
            ('<test><param name="val" label="lab"></param></test>', 0),
            ('<test><param label="lab" name="val"></param></test>', 1),
            (
                """
                <test>
                    <param />
                    <param name="val"/>
                    <param label="lab" name="val"/>
                </test>
                """,
                1,
            ),
            (
                """
                <test>
                    <param label="lab" name="val"/>
                    <param label="lab" name="val"/>
                    <param label="lab" name="val"/>
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
