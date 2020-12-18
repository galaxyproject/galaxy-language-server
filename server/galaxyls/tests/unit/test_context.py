from typing import List, Optional

import pytest
from pygls.workspace import Position
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
        exepected_token = XmlElement()
        expected_line_content = "test"
        expected_position = Position()

        context = XmlContext(
            expected_xsd_element, exepected_token, line_text=expected_line_content, position=expected_position
        )

        assert context.token == exepected_token
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
        position = Position()
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
        assert context.token
        assert context.token.name == expected_token_name
        assert context.token.node_type == expected_node_type
        assert context.xsd_element.name == expected_xsd_node_name
        assert context.stack == expected_stack
