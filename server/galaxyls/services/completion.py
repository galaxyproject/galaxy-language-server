"""Module in charge of the auto-completion feature."""

from typing import Optional

from galaxyls.services.xml.nodes import XmlCDATASection
from pygls.types import (
    CompletionContext,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionTriggerKind,
    InsertTextFormat,
    Position,
    Range,
)

from ..config import CompletionMode
from ..types import AutoCloseTagResult
from .context import XmlContext
from .xsd.parser import XsdAttribute, XsdNode, XsdTree


class XmlCompletionService:
    """Service in charge of generating completion lists based
    on the current XML context.
    """

    def __init__(self, xsd_tree: XsdTree):
        self.xsd_tree: XsdTree = xsd_tree

    def get_completion_at_context(
        self, context: XmlContext, completion_context: CompletionContext, mode: CompletionMode = CompletionMode.AUTO
    ) -> Optional[CompletionList]:
        if isinstance(context.token, XmlCDATASection):
            return None
        triggerKind = completion_context.triggerKind
        if mode == CompletionMode.AUTO and triggerKind == CompletionTriggerKind.TriggerCharacter and not context.is_attribute:
            if completion_context.triggerCharacter == "<":
                return self.get_node_completion(context)
            if completion_context.triggerCharacter == " ":
                return self.get_attribute_completion(context)
        elif triggerKind == CompletionTriggerKind.Invoked:
            if context.is_attribute_value:
                return self.get_attribute_value_completion(context)
            if context.is_tag and not context.is_closing_tag:
                if context.token.name:
                    return self.get_attribute_completion(context)
                return self.get_node_completion(context)
        return None

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
        if context.is_empty or context.is_root:
            result.append(self._build_node_completion_item(context.xsd_element))
        elif context.xsd_element:
            for child in context.xsd_element.children:
                if not context.has_reached_max_occurs(child):
                    result.append(self._build_node_completion_item(child, len(result)))
            result.append(self._build_node_completion_item(self.xsd_tree.expand_element, len(result)))
        return CompletionList(items=result, is_incomplete=False)

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
        if (
            context.is_empty
            or context.is_content
            or context.is_attribute_value
            or context.is_closing_tag
            or not context.token.name
        ):
            return CompletionList(is_incomplete=False)

        result = []
        if context.xsd_element:
            existing_attr_names = context.token.get_attribute_names()
            for attr_name in context.xsd_element.attributes:
                if attr_name in existing_attr_names:
                    continue
                attr = context.xsd_element.attributes[attr_name]
                result.append(self._build_attribute_completion_item(attr, len(result)))
        return CompletionList(items=result, is_incomplete=False)

    def get_attribute_value_completion(self, context: XmlContext) -> CompletionList:
        """Gets a list of possible values for a anumeration restricted attribute if exists.

        Args:
            context (XmlContext): The XML context at an attribute value position.

        Returns:
            CompletionList: The list of possible values of the attribute if it has an enumeration
            restriction.
        """
        if context.attribute_name:
            attribute: Optional[XsdAttribute] = context.xsd_element.attributes.get(context.attribute_name)
            if attribute and attribute.enumeration:
                result = [CompletionItem(item, CompletionItemKind.Value) for item in attribute.enumeration]
                return CompletionList(items=result, is_incomplete=False)
        return CompletionList(False)

    def get_auto_close_tag(self, context: XmlContext, trigger_character: str) -> Optional[AutoCloseTagResult]:
        """Gets the closing result for the currently opened tag in context."""
        if (
            isinstance(context.token, XmlCDATASection)
            or context.is_closing_tag
            or context.is_attribute
            or context.token.is_closed
        ):
            return None

        tag = context.xsd_element.name
        snippet = f"$0</{tag}>"
        replace_range = None
        is_self_closing = trigger_character == "/"
        if is_self_closing:
            start = Position(context.position.line, context.position.character)
            end_character = context.position.character + 1
            if len(context.line_text) > end_character and context.line_text[end_character] == ">":
                end_character = end_character + 1
            end = Position(context.position.line, end_character)
            replace_range = Range(start=start, end=end)
            if not context.is_content:
                snippet = "/>$0"
        elif context.is_content:
            return None

        return AutoCloseTagResult(snippet, replace_range)

    def _build_node_completion_item(self, node: XsdNode, order: int = 0) -> CompletionItem:
        """Generates a completion item with the information about the
        given node definition.

        Args:
            node (XsdNode): The node definition used to build the
            completion item.
            order (int): The position for ordering this item.

        Returns:
            CompletionItem: The completion item with the basic information
            about the node.
        """
        return CompletionItem(
            node.name,
            CompletionItemKind.Class,
            documentation=node.get_doc(),
            sort_text=str(order).zfill(2),
        )

    def _build_attribute_completion_item(self, attr: XsdAttribute, order: int = 0) -> CompletionItem:
        """Generates a completion item with the information about the
        given attribute definition.

        Args:
            attr (XsdAttribute): The attribute definition used to build the
            completion item.
            order (int): The position for ordering this item.

        Returns:
            CompletionItem: The completion item with the basic information
            about the attribute.
        """
        return CompletionItem(
            attr.name,
            CompletionItemKind.Variable,
            documentation=attr.get_doc(),
            insert_text=f'{attr.name}="$1"',
            insert_text_format=InsertTextFormat.Snippet,
            sort_text=str(order).zfill(2),
        )
