"""Module in charge of the auto-completion feature."""

from pygls.types import (
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    InsertTextFormat,
)

from .xsd.parser import XsdTree, XsdNode, XsdAttribute
from .context import XmlContext


class CompletionService:

    xsd_tree: XsdTree

    def __init__(self, xsd_tree: XsdTree):
        self.xsd_tree = xsd_tree

    def get_node_completion(self, context: XmlContext) -> CompletionList:
        result = []
        if context.is_empty:
            result.append(self._build_node_completion_item(context.node))
        elif context.node:
            for child in context.node.children:
                result.append(self._build_node_completion_item(child))
        return CompletionList(False, result)

    def _build_node_completion_item(self, node: XsdNode):
        return CompletionItem(
            node.name, CompletionItemKind.Class, documentation=node.get_doc(),
        )

    def get_attribute_completion(self, context: XmlContext) -> CompletionList:
        result = []
        if context.node:
            for attr_name in context.node.attributes:
                attr = context.node.attributes[attr_name]
                result.append(self._build_attribute_completion_item(attr))
        return CompletionList(False, result)

    def _build_attribute_completion_item(self, attr: XsdAttribute):
        return CompletionItem(
            attr.name,
            CompletionItemKind.Value,
            documentation=attr.get_doc(),
            insert_text=f'{attr.name}="$1"',
            insert_text_format=InsertTextFormat.Snippet,
        )
