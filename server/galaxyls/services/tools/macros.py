from typing import Dict, List, Optional, Set

from pydantic import BaseModel
from pygls.lsp.types import Location
from pygls.workspace import Workspace

from galaxyls.services.tools.constants import MACRO, NAME, TOKEN, XML
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.parser import XmlDocumentParser


class BaseMacrosModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class TokenDefinition(BaseModel):
    name: str
    location: Location
    value: str


class MacroDefinition(BaseModel):
    name: str
    location: Location


class ImportedMacrosFile(BaseMacrosModel):
    file_name: str
    file_uri: Optional[str]
    document: Optional[XmlDocument]
    tokens: Dict[str, TokenDefinition]
    macros: Dict[str, MacroDefinition]


class ToolMacroDefinitions(BaseMacrosModel):
    tool_document: XmlDocument
    imported_macros: Dict[str, ImportedMacrosFile]
    tokens: Dict[str, TokenDefinition]
    macros: Dict[str, MacroDefinition]

    def go_to_import_definition(self, file_name: str) -> Optional[List[Location]]:
        imported_macros = self.imported_macros.get(file_name)
        if imported_macros and imported_macros.document and imported_macros.document.root:
            macros_file_uri = imported_macros.file_uri
            content_range = imported_macros.document.get_element_name_range(imported_macros.document.root)
            if content_range:
                return [
                    Location(
                        uri=macros_file_uri,
                        range=content_range,
                    )
                ]

    def get_token_definition(self, token: str) -> Optional[TokenDefinition]:
        return self.tokens.get(token)

    def get_macro_definition(self, macro_name: str) -> Optional[MacroDefinition]:
        return self.macros.get(macro_name)


class MacroDefinitionsProvider:
    """Provides location information about macros imported by a tool."""

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def load_macro_definitions(self, tool_xml: XmlDocument) -> ToolMacroDefinitions:
        tool = GalaxyToolXmlDocument.from_xml_document(tool_xml)
        tokens = self._get_token_definitions(tool_xml)
        macros = self._get_macro_definitions(tool_xml)
        imported_macro_files = self._get_imported_macro_files_from_tool(tool)
        for file in imported_macro_files.values():
            tokens.update(file.tokens)
            macros.update(file.macros)
        return ToolMacroDefinitions(
            tool_document=tool_xml,
            imported_macros=imported_macro_files,
            tokens=tokens,
            macros=macros,
        )

    def get_macro_names(self, tool_xml: XmlDocument) -> Set[str]:
        tool = GalaxyToolXmlDocument.from_xml_document(tool_xml)
        macros = self._get_macro_definitions(tool_xml)
        imported_macro_files = self._get_imported_macro_files_from_tool(tool)
        for file in imported_macro_files.values():
            macros.update(file.macros)
        return set(macros.keys())

    def _get_imported_macro_files_from_tool(self, tool: GalaxyToolXmlDocument) -> Dict[str, ImportedMacrosFile]:
        macro_files = {}
        uris_dict = tool.get_macro_import_uris()
        for file_name, file_uri in uris_dict.items():
            macros_document = self._load_macros_document(file_uri)
            tokens = self._get_token_definitions(macros_document)
            macros = self._get_macro_definitions(macros_document)
            macro_files[file_name] = ImportedMacrosFile(
                file_name=file_name,
                file_uri=file_uri,
                document=macros_document,
                tokens=tokens,
                macros=macros,
            )
        return macro_files

    def _load_macros_document(self, document_uri: str) -> XmlDocument:
        document = self.workspace.get_document(document_uri)
        xml_document = XmlDocumentParser().parse(document)
        return xml_document

    def _get_token_definitions(self, macros_xml: XmlDocument) -> Dict[str, TokenDefinition]:
        token_elements = macros_xml.find_all_elements_with_name(TOKEN)
        rval = {}
        for element in token_elements:
            token = element.get_attribute(NAME)
            name = token.replace("@", "")
            value = element.get_content(macros_xml.document.source)
            token_def = TokenDefinition(
                name=name,
                location=Location(
                    uri=macros_xml.document.uri,
                    range=macros_xml.get_element_name_range(element),
                ),
                value=value,
            )
            rval[token_def.name] = token_def
        return rval

    def _get_macro_definitions(self, macros_xml: XmlDocument) -> Dict[str, MacroDefinition]:
        macro_elements = macros_xml.find_all_elements_with_name(MACRO)
        xml_elements = macros_xml.find_all_elements_with_name(XML)
        macro_elements += xml_elements
        rval = {}
        for element in macro_elements:
            name = element.get_attribute(NAME)
            macro_def = MacroDefinition(
                name=name,
                location=Location(
                    uri=macros_xml.document.uri,
                    range=macros_xml.get_element_name_range(element),
                ),
            )
            rval[macro_def.name] = macro_def
        return rval
