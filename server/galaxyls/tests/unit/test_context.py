from typing import List, Optional, Tuple

import pytest
from pygls.workspace import Position, Range
from pytest_mock import MockerFixture

from ...services.context import XmlContext, XmlContextService, XsdNode, XsdTree
from ...services.xml.nodes import XmlAttribute, XmlAttributeKey, XmlAttributeValue, XmlElement
from ...services.xml.types import NodeType
from .utils import TestUtils


# [root]
# ├── [child]
# │   └── [subchild]
# └── [sibling]
@pytest.fixture()
def fake_xsd_tree(mocker: MockerFixture) -> XsdTree:
    root = XsdNode(name="root", element=mocker.Mock())
    child = XsdNode(name="child", parent=root, element=mocker.Mock())
    XsdNode(name="sibling", parent=root, element=mocker.Mock())
    XsdNode(name="subchild", parent=child, element=mocker.Mock())
    return XsdTree(root)


class TestXmlContextClass:
    def test_init_sets_properties(self, fake_xsd_tree: XsdTree) -> None:
        expected_xsd_element = fake_xsd_tree.root
        expected_token = XmlElement()
        expected_line_content = "test"
        expected_position = Position(line=0, character=0)

        context = XmlContext(expected_xsd_element, expected_token, line_text=expected_line_content, position=expected_position)

        assert context.node == expected_token
        assert context.xsd_element == expected_xsd_element
        assert context.line_text == expected_line_content
        assert context.position == expected_position
        assert not context.is_empty

    def test_context_with_tag_token_type_returns_is_tag(self, fake_xsd_tree: XsdTree) -> None:
        context = XmlContext(fake_xsd_tree.root, XmlElement())

        assert context.is_tag
        assert not context.is_attribute_key
        assert not context.is_attribute_value

    def test_context_with_attr_key_token_type_returns_is_attr_key(self, fake_xsd_tree: XsdTree) -> None:
        fake_attr = XmlAttribute("attr", 0, 0, XmlElement())
        context = XmlContext(fake_xsd_tree.root, XmlAttributeKey("attr", 0, 0, fake_attr))

        assert not context.is_tag
        assert context.is_attribute_key
        assert not context.is_attribute_value

    def test_context_with_attr_value_token_type_returns_is_attr_value(self, fake_xsd_tree: XsdTree) -> None:
        fake_attr = XmlAttribute("attr", 0, 0, XmlElement())
        context = XmlContext(fake_xsd_tree.root, XmlAttributeValue("val", 0, 0, fake_attr))

        assert not context.is_tag
        assert not context.is_attribute_key
        assert context.is_attribute_value


class TestXmlContextServiceClass:
    def test_init_sets_properties(self, mocker: MockerFixture) -> None:
        expected = mocker.Mock()

        service = XmlContextService(expected)

        assert service.xsd_tree

    def test_get_xml_context_returns_empty_document_context(self, mocker: MockerFixture) -> None:
        empty_xml_content = ""
        position = Position(line=0, character=0)
        xsd_tree_mock = mocker.Mock()
        service = XmlContextService(xsd_tree_mock)

        context = service.get_xml_context(TestUtils.from_source_to_xml_document(empty_xml_content), position)

        assert context.is_empty

    @pytest.mark.parametrize(
        "source_with_mark, expected_token_name, expected_node_type, expected_xsd_node_name, expected_stack",
        [
            ("<root>^", "root", NodeType.ELEMENT, "root", ["root"]),
            ("<root> ^", None, NodeType.CONTENT, "root", ["root"]),
            ("^<root><child", "root", NodeType.ELEMENT, "root", ["root"]),
            ("<root>^<child", "child", NodeType.ELEMENT, "child", ["root", "child"]),
            ("<root>^ <child", None, NodeType.CONTENT, "root", ["root"]),
            ("<root><^child", "child", NodeType.ELEMENT, "child", ["root", "child"]),
            ("<root><child^", "child", NodeType.ELEMENT, "child", ["root", "child"]),
            ("<root><child ^", "child", NodeType.ELEMENT, "child", ["root", "child"]),
            ('<root ^ attr="4"><child ', "root", NodeType.ELEMENT, "root", ["root"]),
            ('<root ^attr="4"><child ', "attr", NodeType.ATTRIBUTE_KEY, "root", ["root"]),
            ('<root attr^="4"><child ', "attr", NodeType.ATTRIBUTE_KEY, "root", ["root"]),
            ('<root attr=^"4"><child ', None, NodeType.ATTRIBUTE_VALUE, "root", ["root"]),
            ('<root attr="4"^><child ', None, NodeType.ATTRIBUTE_VALUE, "root", ["root"]),
            ('<root attr="4" ^><child ', "root", NodeType.ELEMENT, "root", ["root"]),
            ('<root attr="4"><^child ', "child", NodeType.ELEMENT, "child", ["root", "child"]),
            ('<root attr="4">\n<child/^><other', "child", NodeType.ELEMENT, "child", ["root", "child"]),
            ('<root attr="4">\n<child/>^<other', "other", NodeType.ELEMENT, "root", ["root", "other"]),
            ('<root attr="4">\n<child/>^ <other', None, NodeType.CONTENT, "root", ["root"]),
            ('<root attr="4">\n<child/><^other', "other", NodeType.ELEMENT, "root", ["root", "other"]),
            ('<root attr="4">\n<child/><^sibling', "sibling", NodeType.ELEMENT, "sibling", ["root", "sibling"]),
            ('<root attr="4">\n    <^ \n<child', None, NodeType.ELEMENT, "root", ["root"]),
            ('<root attr="4">\n    < \n<^child', "child", NodeType.ELEMENT, "child", ["root", "child"]),
            ("<root><child></child>^", "root", NodeType.ELEMENT, "root", ["root"]),
            ("<root><child><!--^Comment sample--></child>", None, NodeType.COMMENT, "child", ["root", "child"]),
            (
                "<root><child><!--Comment--></child><child><!--^Second comment--></child>",
                None,
                NodeType.COMMENT,
                "child",
                ["root", "child"],
            ),
        ],
    )
    def test_get_xml_context_returns_context_with_expected_node(
        self,
        fake_xsd_tree: XsdTree,
        source_with_mark: str,
        expected_token_name: Optional[str],
        expected_node_type: NodeType,
        expected_xsd_node_name: XsdNode,
        expected_stack: List[str],
    ) -> None:
        service = XmlContextService(fake_xsd_tree)
        position, source = TestUtils.extract_mark_from_source("^", source_with_mark)
        xml_document = TestUtils.from_source_to_xml_document(source)
        print(fake_xsd_tree.render())
        print(f"Test context at position [line={position.line}, char={position.character}]")
        print(f"Document:\n{xml_document.document.source}")

        context = service.get_xml_context(xml_document, position)

        assert context
        assert context.node
        assert context.node.name == expected_token_name
        assert context.node.node_type == expected_node_type
        assert context.stack == expected_stack
        if expected_xsd_node_name is None:
            assert context.xsd_element is None
        else:
            assert context.xsd_element.name == expected_xsd_node_name

    @pytest.mark.parametrize(
        "source_with_mark, expected_token_name, expected_offsets",
        [
            ("<ro^ot></root>", "root", Range(start=Position(line=0, character=1), end=Position(line=0, character=5))),
            ("<root></ro^ot>", "root", Range(start=Position(line=0, character=8), end=Position(line=0, character=12))),
            ("<root>\n</ro^ot>", "root", Range(start=Position(line=1, character=2), end=Position(line=1, character=6))),
        ],
    )
    def test_get_range_for_context_element_returns_expected_offsets(
        self,
        fake_xsd_tree: XsdTree,
        source_with_mark: str,
        expected_token_name: Optional[str],
        expected_offsets: Tuple[int, int],
    ) -> None:
        service = XmlContextService(fake_xsd_tree)
        position, source = TestUtils.extract_mark_from_source("^", source_with_mark)
        xml_document = TestUtils.from_source_to_xml_document(source)
        context = service.get_xml_context(xml_document, position)

        actual_offsets = service.get_range_for_context(xml_document, context)

        assert context.node.name == expected_token_name
        assert actual_offsets == expected_offsets

    @pytest.mark.parametrize(
        "source_with_mark, expected_token_name, expected_offsets",
        [
            (
                '<root at^tr="val"></root>',
                "attr",
                Range(start=Position(line=0, character=6), end=Position(line=0, character=10)),
            ),
            (
                "<root at^tr",
                "attr",
                Range(start=Position(line=0, character=6), end=Position(line=0, character=10)),
            ),
            (
                "<root at^tr=",
                "attr",
                Range(start=Position(line=0, character=6), end=Position(line=0, character=10)),
            ),
            (
                '<root>\n<child a^ttr="val" />\n</root>',
                "attr",
                Range(start=Position(line=1, character=7), end=Position(line=1, character=11)),
            ),
            (
                '<root>\n<child long^_attr="val" />\n</root>',
                "long_attr",
                Range(start=Position(line=1, character=7), end=Position(line=1, character=16)),
            ),
        ],
    )
    def test_get_range_for_context_attribute_returns_expected_offsets(
        self,
        fake_xsd_tree: XsdTree,
        source_with_mark: str,
        expected_token_name: Optional[str],
        expected_offsets: Tuple[int, int],
    ) -> None:
        service = XmlContextService(fake_xsd_tree)
        position, source = TestUtils.extract_mark_from_source("^", source_with_mark)
        xml_document = TestUtils.from_source_to_xml_document(source)
        context = service.get_xml_context(xml_document, position)

        actual_offsets = service.get_range_for_context(xml_document, context)

        assert context.node.name == expected_token_name
        assert actual_offsets == expected_offsets

    @pytest.mark.parametrize(
        "source_with_mark, expected_is_tag_name",
        [
            ("^<root></root>", False),
            ("<^root></root>", True),
            ("<ro^ot></root>", True),
            ("<root^></root>", True),
            ("<root^ ></root>", True),
            ("<root ^></root>", False),
            ("<root>^</root>", False),
            ("<root><^/root>", False),
            ("<root></^root>", False),
            ("<root></root^>", False),
            ("<root ^attr=></root>", False),
            ('<root attr="va^lue"></root>', False),
            ('<root attr="value"^></root>', False),
            ('<root attr="value" ^></root>', False),
        ],
    )
    def test_context_returns_expected_is_tag_name(
        self,
        fake_xsd_tree: XsdTree,
        source_with_mark: str,
        expected_is_tag_name: bool,
    ) -> None:
        service = XmlContextService(fake_xsd_tree)
        position, source = TestUtils.extract_mark_from_source("^", source_with_mark)
        xml_document = TestUtils.from_source_to_xml_document(source)

        context = service.get_xml_context(xml_document, position)

        assert context.is_tag_name == expected_is_tag_name
