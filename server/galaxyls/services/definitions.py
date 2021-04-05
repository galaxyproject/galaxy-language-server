from typing import List, Optional, cast

from pygls.lsp.types import Location, Position
from galaxyls.services.tools.macros import MacroDefinitionsProvider
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.nodes import XmlContent


class DocumentDefinitionsProvider:
    """Provides symbol definition locations."""

    def __init__(self, macro_definitions_provider: MacroDefinitionsProvider) -> None:
        self.macro_definitions_provider = macro_definitions_provider

    def go_to_definition(self, xml_document: XmlDocument, position: Position) -> Optional[List[Location]]:
        offset = xml_document.document.offset_at_position(position)
        node = xml_document.find_node_at(offset)
        if isinstance(node, XmlContent) and node.parent.name == "import":
            content_node = cast(XmlContent, node)
            start, end = content_node.get_content_offsets()
            import_filename = xml_document.get_text_between_offsets(start, end)
            return self.macro_definitions_provider.go_to_import_definition(xml_document, import_filename)
