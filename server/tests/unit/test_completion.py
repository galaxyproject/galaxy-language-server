import pytest
from pytest_mock import MockerFixture
from ...services.completion import (
    AutoCloseTagResult,
    Position,
    Range,
    XmlCompletionService,
    XmlContext,
    XsdTree,
    XsdNode,
    XsdAttribute,
)
from ...services.context import ContextTokenType


@pytest.fixture()
def fake_tree(mocker: MockerFixture) -> XsdTree:
    fake_root = XsdNode("root", element=mocker.Mock())
    fake_attr = XsdAttribute("attr", element=mocker.Mock())
    fake_root.attributes[fake_attr.name] = fake_attr
    XsdNode("child", element=mocker.Mock(), parent=fake_root)
    return XsdTree(fake_root)


@pytest.fixture()
def fake_empty_context(fake_tree: XsdTree) -> XmlContext:
    fake_root = fake_tree.root
    fake_context = XmlContext(is_empty=True)
    fake_context.node = fake_root
    return fake_context


@pytest.fixture()
def fake_invalid_context(fake_tree: XsdTree) -> XmlContext:
    fake_root = fake_tree.root
    fake_context = XmlContext()
    fake_context.is_invalid = True
    fake_context.node = fake_root
    return fake_context


@pytest.fixture()
def fake_context_on_root_node(fake_tree: XsdTree) -> XmlContext:
    fake_root = fake_tree.root
    fake_context = XmlContext()
    fake_context.is_empty = False
    fake_context.token_type = ContextTokenType.TAG
    fake_context.token_name = fake_root.name
    fake_context.node = fake_root
    return fake_context


def get_fake_context_with_line_position(
    fake_tree: XsdTree, line: str, position: Position
) -> XmlContext:
    fake_root = fake_tree.root
    fake_context = XmlContext()
    fake_context.document_line = line
    fake_context.target_position = position
    fake_context.node = fake_root
    return fake_context


class TestXmlCompletionServiceClass:
    def test_init_sets_properties(self, fake_tree: XsdTree) -> None:

        service = XmlCompletionService(fake_tree)

        assert service.xsd_tree

    def test_return_valid_completion_with_node_context(
        self, fake_tree: XsdTree, fake_context_on_root_node
    ) -> None:
        service = XmlCompletionService(fake_tree)

        actual = service.get_node_completion(fake_context_on_root_node)

        assert len(actual.items) == 1
        assert actual.items[0].label == fake_tree.root.children[0].name

    def test_completion_return_root_node_when_empty_context(
        self, fake_tree: XsdTree, fake_empty_context
    ) -> None:
        service = XmlCompletionService(fake_tree)

        actual = service.get_node_completion(fake_empty_context)

        assert len(actual.items) == 1
        assert actual.items[0].label == fake_tree.root.name

    def test_returns_empty_completion_when_invalid_context(
        self, fake_tree: XsdTree, fake_invalid_context
    ) -> None:
        service = XmlCompletionService(fake_tree)

        actual = service.get_node_completion(fake_invalid_context)

        assert len(actual.items) == 0

    def test_return_empty_attribute_completion_when_empty_context(
        self, fake_tree: XsdTree, fake_empty_context
    ) -> None:
        service = XmlCompletionService(fake_tree)

        actual = service.get_attribute_completion(fake_empty_context)

        assert len(actual.items) == 0

    def test_return_valid_attribute_completion_when_node_context(
        self, fake_tree: XsdTree, fake_context_on_root_node
    ) -> None:
        service = XmlCompletionService(fake_tree)

        actual = service.get_attribute_completion(fake_context_on_root_node)

        assert len(actual.items) > 0

    @pytest.mark.parametrize(
        "context_line, position, trigger, expected",
        [
            ("<root>", Position(line=0, character=6), ">", "$0</root>"),
            ("<root/", Position(line=0, character=0), "/", "/>$0"),
        ],
    )
    def test_auto_close_returns_expected_snippet_at_context(
        self,
        fake_tree: XsdTree,
        context_line: str,
        position: Position,
        trigger: str,
        expected: str,
    ) -> None:
        service = XmlCompletionService(fake_tree)
        fake_context = get_fake_context_with_line_position(fake_tree, context_line, position)

        actual = service.get_auto_close_tag(fake_context, trigger)

        assert actual.snippet == expected

    @pytest.mark.parametrize(
        "context_line, position, trigger, expected",
        [
            ("<root>", Position(line=0, character=6), ">", None),
            (
                "<root/",
                Position(line=0, character=5),
                "/",
                Range(Position(character=5), Position(character=6)),
            ),
            (
                "<root/>",
                Position(line=0, character=5),
                "/",
                Range(Position(character=5), Position(character=7)),
            ),
        ],
    )
    def test_auto_close_returns_expected_replace_range_at_context(
        self,
        fake_tree: XsdTree,
        context_line: str,
        position: Position,
        trigger: str,
        expected: str,
    ) -> None:
        service = XmlCompletionService(fake_tree)
        fake_context = get_fake_context_with_line_position(fake_tree, context_line, position)

        actual = service.get_auto_close_tag(fake_context, trigger)

        assert actual.range == expected

    def test_auto_close_returns_none_when_at_node_content(
        self, fake_tree: XsdTree, fake_context_on_root_node: XmlContext
    ) -> None:
        service = XmlCompletionService(fake_tree)
        trigger = ">"
        fake_context = fake_context_on_root_node
        fake_context.is_node_content = True

        actual = service.get_auto_close_tag(fake_context, trigger)

        assert not actual


class TestAutoCloseTagResultClass:
    def test_init_sets_properties(self, mocker: MockerFixture) -> None:
        expected_snippet = "snippet"
        expected_replace_range = mocker.Mock()

        result = AutoCloseTagResult(expected_snippet, expected_replace_range)

        assert result.snippet == expected_snippet
        assert result.range == expected_replace_range
