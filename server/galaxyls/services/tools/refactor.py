from typing import Dict, List, Optional

from lxml import etree
from pydantic.main import BaseModel
from pygls.lsp.types import CodeAction, CodeActionKind, CodeActionParams, TextEdit, WorkspaceEdit
from pygls.lsp.types.basic_structures import Position, Range

from galaxyls.services.tools.constants import DESCRIPTION, MACRO, MACROS, TOOL, XML, XREF
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.tools.macros import ImportedMacrosFile, MacroDefinitionsProvider, ToolMacroDefinitions
from galaxyls.services.xml.document import XmlDocument


class MacroData(BaseModel):
    name: str
    content: str


class RefactorMacrosService:
    def __init__(self, macro_definitions_provider: MacroDefinitionsProvider) -> None:
        self.definitions_provider = macro_definitions_provider

    def create_extract_to_local_macro_actions(
        self, xml_document: XmlDocument, macro: MacroData, params: CodeActionParams
    ) -> List[CodeAction]:
        return [
            CodeAction(
                title="Extract to local macro",
                kind=CodeActionKind.RefactorExtract,
                edit=WorkspaceEdit(changes=self._calculate_local_changes_for_macro(xml_document, macro, params)),
            )
        ]

    def create_extract_to_macros_file_actions(
        self, macro_definitions: ToolMacroDefinitions, macro: MacroData, params: CodeActionParams
    ) -> List[CodeAction]:
        code_actions = []

        for file_name, macro_file_definition in macro_definitions.imported_macros.items():
            code_actions.append(
                CodeAction(
                    title=f"Extract to macro in {file_name}",
                    kind=CodeActionKind.RefactorExtract,
                    edit=WorkspaceEdit(
                        changes=self._calculate_external_changes_for_macro(macro_file_definition, macro, params)
                    ),
                )
            )

        return code_actions

    def _calculate_local_changes_for_macro(
        self, xml_document: XmlDocument, macro: MacroData, params: CodeActionParams
    ) -> Dict[str, TextEdit]:
        tool = GalaxyToolXmlDocument.from_xml_document(xml_document)
        macros_element = tool.get_macros_element()
        edits: List[TextEdit] = []
        if macros_element is None:
            edits.append(self._edit_create_with_macros_section(tool, macro))
        else:
            edits.append(self._edit_add_macro_to_macros_section(tool, macro))
        edits.append(self._edit_replace_range_with_macro_expand(macro, params.range))
        changes = {params.text_document.uri: edits}
        return changes

    def _calculate_external_changes_for_macro(
        self, macro_file_definition: ImportedMacrosFile, macro: MacroData, params: CodeActionParams
    ) -> Dict[str, TextEdit]:
        macros_xml_doc = macro_file_definition.document
        macros_root = macros_xml_doc.root
        macros_content_range = macros_xml_doc.get_content_range(macros_root)
        insert_range = Range(start=macros_content_range.end, end=macros_content_range.end)
        external_edit = TextEdit(
            range=insert_range,
            new_text=f'<xml name="{macro.name}">\n{macro.content}\n</xml>\n',
        )
        changes = {
            params.text_document.uri: [self._edit_replace_range_with_macro_expand(macro, params.range)],
            macro_file_definition.file_uri: [external_edit],
        }
        return changes

    def _edit_replace_range_with_macro_expand(self, macro: MacroData, range: Range) -> TextEdit:
        return TextEdit(
            range=range,
            new_text=f'<expand macro="{macro.name}"/>',
        )

    def _edit_create_with_macros_section(self, tool: GalaxyToolXmlDocument, macro: MacroData) -> TextEdit:
        insert_position = self._find_macros_insert_position(tool)
        insert_range = Range(start=insert_position, end=insert_position)
        return TextEdit(
            range=insert_range,
            new_text=f'\n<macros>\n<xml name="{macro.name}">\n{macro.content}\n</xml>\n</macros>',
        )

    def _edit_add_macro_to_macros_section(self, tool: GalaxyToolXmlDocument, macro: MacroData) -> TextEdit:
        macros_element = tool.get_macros_element()
        macros_content_range = tool.get_content_range(macros_element)
        insert_range = Range(start=macros_content_range.end, end=macros_content_range.end)
        return TextEdit(
            range=insert_range,
            new_text=f'<xml name="{macro.name}">\n{macro.content}\n</xml>\n',
        )

    def _find_macros_insert_position(self, tool: GalaxyToolXmlDocument) -> Position:
        """Returns the position inside the document where the macros section
        can be inserted.

        Returns:
            Range: The position where the macros section can be inserted in the document.
        """
        section = tool.find_element(XREF)
        if section:
            return tool.get_position_after(section)
        section = tool.find_element(DESCRIPTION)
        if section:
            return tool.get_position_after(section)
        return tool.get_content_range(TOOL).start


class RefactoringService:
    def __init__(self, macros_refactoring_service: RefactorMacrosService) -> None:
        self.macros = macros_refactoring_service

    def get_available_refactoring_actions(self, xml_document: XmlDocument, params: CodeActionParams) -> List[CodeAction]:
        code_actions = []
        text_in_range = xml_document.get_text_in_range(params.range)
        target_element_tag = self.get_valid_full_element_tag(text_in_range)
        if target_element_tag is not None:
            macro = MacroData(name=target_element_tag, content=text_in_range.strip())
            macro_definitions = self.macros.definitions_provider.load_macro_definitions(xml_document)
            code_actions.extend(self.macros.create_extract_to_macros_file_actions(macro_definitions, macro, params))
            code_actions.extend(self.macros.create_extract_to_local_macro_actions(xml_document, macro, params))
        return code_actions

    def get_valid_full_element_tag(self, xml_text: str) -> Optional[str]:
        stripped_xml = xml_text.strip()
        if len(stripped_xml) < 5 or (stripped_xml[0] != "<" or stripped_xml[-1] != ">"):
            # Too short to be an element or doesn't look like an element
            return None
        return self._get_valid_node_tag(stripped_xml)

    def _get_valid_node_tag(self, stripped_xml: str) -> Optional[str]:
        try:
            xml_in_range = etree.fromstring(stripped_xml, etree.XMLParser(strip_cdata=False))
            if xml_in_range.tag in [TOOL, MACROS, MACRO, XML]:
                return None
            return xml_in_range.tag
        except BaseException as e:
            print(e)
            return None
