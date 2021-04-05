from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel
from pygls.lsp.types import Location
from pygls.workspace import Workspace

from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.parser import XmlDocumentParser


class BaseMacrosModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class ImportedMacrosFile(BaseMacrosModel):
    file_name: str
    file_uri: Optional[str]
    document: Optional[XmlDocument]


class ToolMacroDefinitions(BaseMacrosModel):
    tool_document: XmlDocument
    imported_macros: Dict[str, ImportedMacrosFile]


class MacroDefinitionsProvider:
    """Provides location information about macros imported by a tool."""

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.documents: Dict[str, ToolMacroDefinitions] = {}

    def register_document(self, tool_xml: XmlDocument):
        imported_macro_files = self._get_imported_macro_files_from_tool(tool_xml)
        self.documents[tool_xml.document.uri] = ToolMacroDefinitions(
            tool_document=tool_xml, imported_macros=imported_macro_files
        )

    def go_to_import_definition(self, tool_xml: XmlDocument, file_name: str) -> Optional[List[Location]]:
        self.register_document(tool_xml)
        definitions = self.documents.get(tool_xml.document.uri)
        imported_macros = definitions.imported_macros.get(file_name)
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

    def _get_imported_macro_files_from_tool(self, tool_xml: XmlDocument) -> Dict[str, ImportedMacrosFile]:
        tool_directory = self._get_tool_directory(tool_xml)
        macro_files = {}
        import_elements = tool_xml.find_all_elements_with_name("import")
        for imp in import_elements:
            name = imp.get_content(tool_xml.document.source)
            if name:
                path = tool_directory / name
                file_uri = None
                macros_document = None
                if path.exists():
                    file_uri = path.as_uri()
                    macros_document = self._load_macros_document(file_uri)
                macro_files[name] = ImportedMacrosFile(
                    file_name=name,
                    file_uri=file_uri,
                    document=macros_document,
                )
        return macro_files

    def _get_tool_directory(self, tool_xml: XmlDocument):
        tool_directory = Path(tool_xml.document.path).resolve().parent
        return tool_directory

    def _load_macros_document(self, document_uri: str) -> Optional[XmlDocument]:
        document = self.workspace.get_document(document_uri)
        xml_document = XmlDocumentParser().parse(document)
        return xml_document
