from typing import List, Optional, cast

from pygls.lsp.types import Location, Position
from galaxyls.services.tools.macros import MacroDefinitionsProvider, TokenDefinition
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.nodes import XmlContent


class DocumentDefinitionsProvider:
    """Provides symbol definition locations."""

    def __init__(self, macro_definitions_provider: MacroDefinitionsProvider) -> None:
        self.macro_definitions_provider = macro_definitions_provider

    def go_to_definition(self, xml_document: XmlDocument, position: Position) -> Optional[List[Location]]:
        macro_definitions = self.macro_definitions_provider.load_macro_definitions(xml_document)
        word = xml_document.document.word_at_position(position)
        token_definition = macro_definitions.get_token_definition(word)
        if token_definition:
            return [token_definition.location]

        macro_definition = macro_definitions.get_macro_definition(word)
        if macro_definition:
            return [macro_definition.location]

        offset = xml_document.document.offset_at_position(position)
        node = xml_document.find_node_at(offset)
        if isinstance(node, XmlContent) and node.parent.name == "import":
            content_node = cast(XmlContent, node)
            start, end = content_node.get_content_offsets()
            import_filename = xml_document.get_text_between_offsets(start, end)
            return macro_definitions.go_to_import_definition(import_filename)

    def get_token_definition(self, xml_document: XmlDocument, token: str) -> Optional[TokenDefinition]:
        macro_definitions = self.macro_definitions_provider.load_macro_definitions(xml_document)
        return macro_definitions.get_token_definition(token)
