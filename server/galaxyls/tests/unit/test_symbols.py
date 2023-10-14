from galaxyls.services.symbols import DocumentSymbolsProvider
from galaxyls.tests.unit.utils import TestUtils

FIELD_SYMBOL_KIND = 8  # SymbolKind.Field
PROPERTY_SYMBOL_KIND = 7  # SymbolKind.Property


def test_get_document_symbols():
    xml_document = TestUtils.from_source_to_xml_document("<tool></tool>")
    provider = DocumentSymbolsProvider()
    symbols = provider.get_document_symbols(xml_document)
    assert len(symbols) == 1
    assert symbols[0].name == "tool"
    assert symbols[0].kind == FIELD_SYMBOL_KIND
    assert len(symbols[0].children) == 0


def test_get_element_children_symbols():
    xml_document = TestUtils.from_source_to_xml_document("<tool><command></command></tool>")
    provider = DocumentSymbolsProvider()
    symbols = provider.get_document_symbols(xml_document)
    element_symbol = symbols[0]
    children_symbols = element_symbol.children
    assert len(children_symbols) == 1
    assert children_symbols[0].name == "command"
    assert children_symbols[0].kind == FIELD_SYMBOL_KIND


def test_get_attribute_symbol_definition():
    xml_document = TestUtils.from_source_to_xml_document("<tool><command executable='true'></command></tool>")
    provider = DocumentSymbolsProvider()
    symbols = provider.get_document_symbols(xml_document)
    attribute_symbol = symbols[0].children[0].children[0]
    assert attribute_symbol.name == "executable"
    assert attribute_symbol.kind == PROPERTY_SYMBOL_KIND


def test_get_element_symbol_detail():
    xml_document = TestUtils.from_source_to_xml_document('<tool id="TEST"></tool>')
    provider = DocumentSymbolsProvider()
    symbols = provider.get_document_symbols(xml_document)
    assert len(symbols) == 1
    element_symbol = symbols[0]
    assert element_symbol.detail == "TEST"
