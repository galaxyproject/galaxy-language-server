"""Module in charge of the auto-completion feature."""

from pygls.types import (
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    InsertTextFormat,
)

from .xsd.parser import XsdTree, XsdNode, XsdAttribute
from .context import XmlContext


class XmlCompletionService:
    """Service in charge of generating completion lists based
    on the current XML context.
    """

    xsd_tree: XsdTree

    def __init__(self, xsd_tree: XsdTree):
        self.xsd_tree = xsd_tree

    def get_node_completion(self, context: XmlContext) -> CompletionList:
        """Gets a list of completion items with all the available child tags
        that can be placed in the current context node.

        Args:
            context (XmlContext): The XML context information at a specific
            document position. It should contain, at least, the current node.

        Returns:
            CompletionList: A list of completion items with the child nodes
            that can be placed under the current node.
        """
        result = []
        if context.is_empty:
            result.append(self._build_node_completion_item(context.node))
        elif context.node:
            for child in context.node.children:
                result.append(self._build_node_completion_item(child))
        return CompletionList(items=result, is_incomplete=False)

    def _build_node_completion_item(self, node: XsdNode) -> CompletionItem:
        """Generates a completion item with the information about the
        given node definition.

        Args:
            node (XsdNode): The node definition used to build the
            completion item.

        Returns:
            CompletionItem: The completion item with the basic information
            about the node.
        """
        return CompletionItem(
            node.name, CompletionItemKind.Class, documentation=node.get_doc(),
        )

    def get_attribute_completion(self, context: XmlContext) -> CompletionList:
        """Gets a list of completion items with all the attributes that can be
        used in the current context node.

        Args:
            context (XmlContext): The XML context information at a specific
            document position. It should contain, at least, the current node.

        Returns:
            CompletionList: The completion item with the basic information
            about the attributes.
        """
        result = []
        if not context.is_empty:
            if context.node:
                for attr_name in context.node.attributes:
                    attr = context.node.attributes[attr_name]
                    result.append(self._build_attribute_completion_item(attr))
        return CompletionList(items=result, is_incomplete=False)

    def _build_attribute_completion_item(
        self, attr: XsdAttribute
    ) -> CompletionItem:
        """Generates a completion item with the information about the
        given attribute definition.

        Args:
            attr (XsdAttribute): The attribute definition used to build the
            completion item.

        Returns:
            CompletionItem: The completion item with the basic information
            about the attribute.
        """
        return CompletionItem(
            attr.name,
            CompletionItemKind.Value,
            documentation=attr.get_doc(),
            insert_text=f'{attr.name}="$1"',
            insert_text_format=InsertTextFormat.Snippet,
        )
