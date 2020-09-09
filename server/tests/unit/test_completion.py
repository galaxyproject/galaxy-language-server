import pytest
from pytest_mock import MockerFixture
from ...services.completion import (
    XmlCompletionService,
    XmlContext,
    XsdTree,
    XsdNode,
    XsdAttribute,
)
from ...services.context import ContextTokenType


@pytest.fixture()
def fake_tree(mocker: MockerFixture):
    fake_root = XsdNode("root", element=mocker.Mock())
    fake_attr = XsdAttribute("attr", element=mocker.Mock())
    fake_root.attributes[fake_attr.name] = fake_attr
    XsdNode("child", element=mocker.Mock(), parent=fake_root)
    return XsdTree(fake_root)


@pytest.fixture()
def fake_empty_context(fake_tree):
    fake_root = fake_tree.root
    fake_context = XmlContext(is_empty=True)
    fake_context.node = fake_root
    return fake_context


@pytest.fixture()
def fake_context_on_root_node(fake_tree):
    fake_root = fake_tree.root
    fake_context = XmlContext()
    fake_context.is_empty = False
    fake_context.token_type = ContextTokenType.TAG
    fake_context.token_name = fake_root.name
    fake_context.node = fake_root
    return fake_context


class TestXmlCompletionServiceClass:
    def test_init_sets_properties(self, fake_tree) -> None:

        service = XmlCompletionService(fake_tree)

        assert service.xsd_tree

    def test_return_valid_completion_with_node_context(
        self, fake_tree, fake_context_on_root_node
    ) -> None:
        service = XmlCompletionService(fake_tree)

        actual = service.get_node_completion(fake_context_on_root_node)

        assert len(actual.items) == 1
        assert actual.items[0].label == fake_tree.root.children[0].name

    def test_completion_return_root_node_when_empty_context(
        self, fake_tree, fake_empty_context
    ) -> None:
        service = XmlCompletionService(fake_tree)

        actual = service.get_node_completion(fake_empty_context)

        assert len(actual.items) == 1
        assert actual.items[0].label == fake_tree.root.name

    def test_return_empty_attribute_completion_when_empty_context(
        self, fake_tree, fake_empty_context
    ) -> None:
        service = XmlCompletionService(fake_tree)

        actual = service.get_attribute_completion(fake_empty_context)

        assert len(actual.items) == 0

    def test_return_valid_attribute_completion_when_node_context(
        self, fake_tree, fake_context_on_root_node
    ) -> None:
        service = XmlCompletionService(fake_tree)

        actual = service.get_attribute_completion(fake_context_on_root_node)

        assert len(actual.items) > 0
