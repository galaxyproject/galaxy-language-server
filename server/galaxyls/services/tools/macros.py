from typing import Dict, List, Optional, Set

from pydantic import BaseModel
from pygls.lsp.types import Location
from pygls.workspace import Workspace

from galaxyls.services.tools.constants import MACRO, NAME, TOKEN, XML
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.nodes import XmlElement
from galaxyls.services.xml.parser import XmlDocumentParser


class BaseMacrosModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class TokenDefinition(BaseModel):
    name: str
    location: Location
    value: str


class TokenParam(TokenDefinition):
    param_name: str
    default_value: str


class MacroDefinition(BaseModel):
    name: str
    location: Location
    token_params: Dict[str, TokenParam]


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
            content_range = imported_macros.document.get_full_range(imported_macros.document.root)
            if content_range:
                return [
                    Location(
                        uri=macros_file_uri,
                        range=content_range,
                    )
                ]

    def get_token_definition(self, token: str) -> Optional[TokenDefinition]:
        definition = self.tokens.get(token)
        if definition is None:
            return self.get_token_param_definition(token)
        return definition

    def get_token_param_definition(self, token: str) -> Optional[TokenParam]:
        for macro in self.macros.values():
            if token in macro.token_params:
                return macro.token_params.get(token)
        return None

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

    def get_macro_token_params(self, tool_xml: XmlDocument, macro_name: str) -> List[TokenParam]:
        macro_definitions = self.load_macro_definitions(tool_xml)
        macro = macro_definitions.get_macro_definition(macro_name)
        if macro.token_params:
            return list(macro.token_params.values())
        return []

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
                    range=macros_xml.get_full_range(element),
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
                    range=macros_xml.get_full_range(element),
                ),
                token_params=self.get_token_params(macros_xml, element),
            )
            rval[macro_def.name] = macro_def
        return rval

    def get_token_params(self, macros_xml: XmlDocument, element: XmlElement) -> Dict[str, TokenParam]:
        token_params = {}
        for attr_name, attr in element.attributes.items():
            if attr_name.startswith("token_"):
                param_name = attr_name.replace("token_", "")
                token_name = param_name.upper()
                default_value = attr.get_value()
                token_param = TokenParam(
                    name=token_name,
                    param_name=param_name,
                    default_value=default_value,
                    value=f"**Token parameter**\n- Default value: `{default_value}`",
                    location=Location(
                        uri=macros_xml.document.uri,
                        range=macros_xml.get_full_range(attr),
                    ),
                )
                token_params[token_name] = token_param
        return token_params
