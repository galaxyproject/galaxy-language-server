"""Module in charge of the auto-completion feature."""

from typing import Optional, cast

from galaxyls.services.definitions import DocumentDefinitionsProvider
from galaxyls.services.xml.nodes import XmlCDATASection, XmlElement
from pygls.lsp.types import (
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

    def __init__(self, xsd_tree: XsdTree, definitions_provider: DocumentDefinitionsProvider):
        self.xsd_tree: XsdTree = xsd_tree
        self.definitions_provider = definitions_provider

    def get_completion_at_context(
        self, context: XmlContext, completion_context: CompletionContext, mode: CompletionMode = CompletionMode.AUTO
    ) -> Optional[CompletionList]:
        if isinstance(context.node, XmlCDATASection):
            return None
        triggerKind = completion_context.trigger_kind
        if mode == CompletionMode.AUTO and triggerKind == CompletionTriggerKind.TriggerCharacter and not context.is_attribute:
            if completion_context.trigger_character == "<":
                return self.get_node_completion(context)
            if completion_context.trigger_character == " ":
                return self.get_attribute_completion(context)
        elif triggerKind == CompletionTriggerKind.Invoked:
            if context.is_inside_attribute_value:
                return self.get_attribute_value_completion(context)
            if context.is_attribute_key:
                return self.get_attribute_completion(context)
            if context.is_tag and not context.is_closing_tag and not context.is_at_end:
                if context.is_valid_tag() and not context.is_tag_name:
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
            result.append(self._build_node_completion_item(self.xsd_tree.root))
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
            or not context.node.name
        ):
            return CompletionList(is_incomplete=False)

        result = []
        if context.xsd_element:
            existing_attr_names = context.node.get_attribute_names()
            for attr_name in context.xsd_element.attributes:
                if attr_name in existing_attr_names:
                    continue
                attr = context.xsd_element.attributes[attr_name]
                result.append(self._build_attribute_completion_item(attr, len(result)))
            if context.node.name == "expand":
                element = cast(XmlElement, context.node)
                macro_name = element.get_attribute("macro")
                if macro_name:
                    token_params = self.definitions_provider.macro_definitions_provider.get_macro_token_params(
                        context.xml_document, macro_name
                    )
                    for token in token_params:
                        if token.param_name in existing_attr_names:
                            continue
                        result.append(
                            CompletionItem(
                                label=token.param_name,
                                kind=CompletionItemKind.Variable,
                                insert_text=f'{token.param_name}="${{1:{token.default_value}}}"',
                                insert_text_format=InsertTextFormat.Snippet,
                                sort_text=str(len(result)).zfill(2),
                            )
                        )
        return CompletionList(items=result, is_incomplete=False)

    def get_attribute_value_completion(self, context: XmlContext) -> CompletionList:
        """Gets a list of possible values for an enumeration restricted attribute if exists.

        Args:
            context (XmlContext): The XML context at an attribute value position.

        Returns:
            CompletionList: The list of possible values of the attribute if it has an enumeration
            restriction.
        """
        if context.attribute_name:
            attribute = context.xsd_element.attributes.get(context.attribute_name)
            if attribute and attribute.enumeration:
                result = [CompletionItem(label=item, kind=CompletionItemKind.Value) for item in attribute.enumeration]
                return CompletionList(items=result, is_incomplete=False)
            if attribute and attribute.name == "macro":
                macro_names = self.definitions_provider.macro_definitions_provider.get_macro_names(context.xml_document)
                result = [CompletionItem(label=item, kind=CompletionItemKind.Value) for item in macro_names]
                return CompletionList(items=result, is_incomplete=False)
        return CompletionList(is_incomplete=False)

    def get_auto_close_tag(self, context: XmlContext, trigger_character: str) -> Optional[AutoCloseTagResult]:
        """Gets the closing result for the currently opened tag in context.

        The `context` parameter should be placed right before the trigger_character, otherwise the context
        information will be located at the trigger_character itself which doesn't provide the real context."""
        if (
            isinstance(context.node, XmlCDATASection)
            or context.is_closing_tag
            or context.node.is_closed
            or (context.is_attribute and not context.is_attribute_end)
            or context.characted_at_position == ">"
        ):
            return None

        tag = context.xsd_element.name
        snippet = f"$0</{tag}>"
        replace_range = None
        is_self_closing = trigger_character == "/"
        if is_self_closing:
            # Build the position Range to be replaced by the snippet
            # Get the document position of the trigger_character => +1 character from current context.position
            start = Position(line=context.position.line, character=context.position.character + 1)
            # Check if there is a `>` already after the `/` trigger and include it in the Range to avoid duplication
            end_character = context.position.character + 2
            if len(context.line_text) > end_character and context.line_text[end_character] == ">":
                end_character = end_character + 1
            end = Position(line=context.position.line, character=end_character)
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
            label=node.name,
            kind=CompletionItemKind.Class,
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
            label=attr.name,
            kind=CompletionItemKind.Variable,
            documentation=attr.get_doc(),
            insert_text=f'{attr.name}="$1"',
            insert_text_format=InsertTextFormat.Snippet,
            sort_text=str(order).zfill(2),
        )
