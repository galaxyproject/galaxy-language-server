from typing import (
    List,
    Optional,
)

from lsprotocol.types import (
    DocumentSymbol,
    SymbolKind,
)

from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.nodes import (
    XmlAttribute,
    XmlElement,
    XmlSyntaxNode,
)
from galaxyls.services.xml.utils import convert_document_offsets_to_range


class DocumentSymbolsProvider:
    """Provides symbols defined in the tool document."""

    def get_document_symbols(self, xml_document: XmlDocument) -> List[DocumentSymbol]:
        """Gets all symbols defined in the tool document in a hierarchical structure."""
        if xml_document.root is None:
            return []
        return [self._get_element_symbol_definition(xml_document, xml_document.root)]

    def _get_element_children_symbols(self, element: XmlElement, xml_document: XmlDocument) -> List[DocumentSymbol]:
        result: List[DocumentSymbol] = []
        for child in element.children:
            if isinstance(child, XmlAttribute):
                result.append(self._get_attribute_symbol_definition(xml_document, child))
            if isinstance(child, XmlElement):
                result.append(self._get_element_symbol_definition(xml_document, child))
        return result

    def _get_element_symbol_definition(self, xml_document: XmlDocument, element: XmlElement) -> DocumentSymbol:
        element_range = convert_document_offsets_to_range(xml_document.document, element.start, element.end)
        return DocumentSymbol(
            name=self._get_node_name(element),
            kind=SymbolKind.Field,
            detail=self._get_element_symbol_detail(element, xml_document),
            range=element_range,
            selection_range=element_range,
            children=self._get_element_children_symbols(element, xml_document),
        )

    def _get_attribute_symbol_definition(self, xml_document: XmlDocument, attribute: XmlAttribute) -> DocumentSymbol:
        attribute_range = convert_document_offsets_to_range(xml_document.document, attribute.start, attribute.end)
        return DocumentSymbol(
            name=self._get_node_name(attribute),
            kind=SymbolKind.Property,
            detail=attribute.value.unquoted if attribute.value else None,
            range=attribute_range,
            selection_range=attribute_range,
        )

    def _get_node_name(self, node: XmlSyntaxNode) -> str:
        return node.name or ""

    def _get_element_symbol_detail(self, element: XmlElement, xml_document: XmlDocument) -> Optional[str]:
        if element.name in ["option", "when", "add", "remove"]:
            detail = element.get_attribute_value("value")
        elif element.name in ["citation", "validator"]:
            detail = element.get_attribute_value("type")
        elif element.name in ["requirement", "import"]:
            detail = element.get_content(xml_document.document.source)
        elif element.name in ["expand"]:
            detail = element.get_attribute_value("macro")
        else:
            detail = element.get_attribute_value("id") or element.get_attribute_value("name")
        return detail
