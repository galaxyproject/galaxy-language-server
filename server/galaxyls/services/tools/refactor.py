from pathlib import Path
from typing import Dict, List, Optional, Set, Union
from urllib.parse import urlparse

from lxml import etree
from pydantic.main import BaseModel
from pygls.lsp.types import (
    CodeAction,
    CodeActionKind,
    CodeActionParams,
    CreateFile,
    Position,
    Range,
    ResourceOperationKind,
    TextDocumentEdit,
    TextEdit,
    VersionedTextDocumentIdentifier,
    WorkspaceEdit,
)
from pygls.workspace import Workspace

from galaxyls.services.format import GalaxyToolFormatService
from galaxyls.services.tools.constants import DESCRIPTION, MACRO, MACROS, TOOL, XML, XREF
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.tools.macros import ImportedMacrosFile, MacroDefinitionsProvider, ToolMacroDefinitions
from galaxyls.services.xml.document import XmlDocument

DEFAULT_MACROS_FILENAME = "macros.xml"
EXCLUDED_TAGS = {TOOL, MACROS, MACRO, XML}


class MacroData(BaseModel):
    name: str
    content: str


class RefactorMacrosService:
    """Refactoring operations in the context of macros."""

    def __init__(
        self,
        workspace: Workspace,
        macro_definitions_provider: MacroDefinitionsProvider,
        format_service: GalaxyToolFormatService,
    ) -> None:
        self.workspace = workspace
        self.definitions_provider = macro_definitions_provider
        self.format_service = format_service

    def create_extract_to_local_macro_actions(
        self, tool: GalaxyToolXmlDocument, macro: MacroData, params: CodeActionParams
    ) -> List[CodeAction]:
        """Returns refactoring actions to extract a macro into the local <macros> section of a tool wrapper."""
        return [
            CodeAction(
                title="Extract to local macro",
                kind=CodeActionKind.RefactorExtract,
                edit=WorkspaceEdit(changes=self._calculate_local_changes_for_macro(tool, macro, params)),
            )
        ]

    def create_extract_to_macros_file_actions(
        self, tool: GalaxyToolXmlDocument, macro_definitions: ToolMacroDefinitions, macro: MacroData, params: CodeActionParams
    ) -> List[CodeAction]:
        """Returns refactoring actions for extracting a macro into an external macros definition file."""
        if not macro_definitions.imported_macros:
            return [
                CodeAction(
                    title=f"Extract to macro, create and import {DEFAULT_MACROS_FILENAME}",
                    kind=CodeActionKind.RefactorExtract,
                    edit=WorkspaceEdit(
                        document_changes=self._calculate_external_changes_for_macro_in_new_file(
                            tool, DEFAULT_MACROS_FILENAME, macro, params
                        )
                    ),
                )
            ]
        code_actions = []
        for file_name, macro_file_definition in macro_definitions.imported_macros.items():
            code_actions.append(
                CodeAction(
                    title=f"Extract to macro in {file_name}",
                    kind=CodeActionKind.RefactorExtract,
                    edit=WorkspaceEdit(
                        changes=self._calculate_external_changes_for_macro(tool, macro_file_definition, macro, params)
                    ),
                )
            )

        return code_actions

    def _calculate_local_changes_for_macro(
        self, tool: GalaxyToolXmlDocument, macro: MacroData, params: CodeActionParams
    ) -> Dict[str, TextEdit]:
        """Returns a dictionary with the file uri and the TextEdit operations that will add a macro definition to
        the <macros> section of a tool wrapper. If the <macros> section doesn't exists it will also be created."""
        macros_element = tool.get_macros_element()
        edits: List[TextEdit] = []
        if macros_element is None:
            edits.append(self._edit_create_with_macros_section(tool, macro))
        else:
            edits.append(self._edit_add_macro_to_macros_section(tool, macro))
        edits.append(self._edit_replace_range_with_macro_expand(tool, macro, params.range))
        changes = {params.text_document.uri: edits}
        return changes

    def _calculate_external_changes_for_macro(
        self,
        tool: GalaxyToolXmlDocument,
        macro_file_definition: ImportedMacrosFile,
        macro: MacroData,
        params: CodeActionParams,
    ) -> Dict[str, TextEdit]:
        """Returns a dictionary with the document uri and the collection of TextEdit operations for that particular document.

        The edits will add the macro definition to the given imported macros file and replace the refactored macro with the
        corresponding <expand> element in the tool wrapper."""
        macros_xml_doc = macro_file_definition.document
        macros_root = macros_xml_doc.root
        insert_position = macros_xml_doc.get_position_after_last_child(macros_root)
        insert_range = Range(start=insert_position, end=insert_position)
        macro_xml = f'<xml name="{macro.name}">\n{macro.content}\n</xml>'
        final_macro_xml = self._adapt_format(macros_xml_doc, insert_range, macro_xml)
        external_edit = TextEdit(
            range=insert_range,
            new_text=final_macro_xml,
        )
        changes = {
            params.text_document.uri: [self._edit_replace_range_with_macro_expand(tool, macro, params.range)],
            macro_file_definition.file_uri: [external_edit],
        }
        return changes

    def _calculate_external_changes_for_macro_in_new_file(
        self, tool: GalaxyToolXmlDocument, new_file_name: str, macro: MacroData, params: CodeActionParams
    ) -> List[Union[CreateFile, TextDocumentEdit]]:
        """Returns a list of workspace document changes that will create a new macros.xml file with the given
        macro definition inside and also import the newly created file in the tool wrapper."""
        base_path = Path(urlparse(tool.xml_document.document.uri).path).parent
        new_file_uri = (base_path / new_file_name).as_uri()
        xml_content = f'<macros>\n<xml name="{macro.name}">\n{macro.content}\n</xml>\n</macros>'
        final_xml_content = self.format_service.format_content(xml_content)
        new_doc_insert_position = Position(line=0, character=0)
        tool_document = self.workspace.get_document(params.text_document.uri)
        changes = [
            CreateFile(uri=new_file_uri, kind=ResourceOperationKind.Create),
            TextDocumentEdit(
                text_document=VersionedTextDocumentIdentifier(
                    uri=new_file_uri,
                    version=0,
                ),
                edits=[
                    TextEdit(
                        range=Range(start=new_doc_insert_position, end=new_doc_insert_position),
                        new_text=final_xml_content,
                    ),
                ],
            ),
            TextDocumentEdit(
                text_document=VersionedTextDocumentIdentifier(
                    uri=tool_document.uri,
                    version=tool_document.version,
                ),
                edits=[
                    self._edit_create_import_macros_section(tool, DEFAULT_MACROS_FILENAME),
                    self._edit_replace_range_with_macro_expand(tool, macro, params.range),
                ],
            ),
        ]
        return changes

    def _edit_replace_range_with_macro_expand(self, tool: GalaxyToolXmlDocument, macro: MacroData, range: Range) -> TextEdit:
        """Returns the TextEdit operation that will replace the refactored macro with the corresponding <expand> element."""
        indentation = tool.xml_document.get_line_indentation(range.start.line)
        return TextEdit(
            range=self._get_range_from_line_start(range),
            new_text=f'{indentation}<expand macro="{macro.name}"/>',
        )

    def _edit_create_import_macros_section(self, tool: GalaxyToolXmlDocument, macros_file_name: str) -> TextEdit:
        """Returns the TextEdit operation that will add a macros file <import> definition to the existing
        <macros> section of a tool wrapper or also create the <macros> section if it doesn't exists."""
        macros_element = tool.find_element(MACROS)
        if macros_element:
            insert_position = tool.get_position_before_first_child(macros_element)
            macro_xml = f"<import>{macros_file_name}</import>"
        else:
            insert_position = self._find_macros_insert_position(tool)
            macro_xml = f"<macros>\n<import>{macros_file_name}</import>\n</macros>"
        insert_range = Range(start=insert_position, end=insert_position)
        final_macro_xml = self._adapt_format(tool.xml_document, insert_range, macro_xml)
        return TextEdit(
            range=insert_range,
            new_text=final_macro_xml,
        )

    def _edit_create_with_macros_section(self, tool: GalaxyToolXmlDocument, macro: MacroData) -> TextEdit:
        """Returns the TextEdit operation that will add a local <macros> section inside the tool wrapper along with
        the macro provided."""
        insert_position = self._find_macros_insert_position(tool)
        insert_range = Range(start=insert_position, end=insert_position)
        macro_xml = f'<macros>\n<xml name="{macro.name}">\n{macro.content}\n</xml>\n</macros>'
        final_macro_xml = self._adapt_format(tool.xml_document, insert_range, macro_xml)
        return TextEdit(
            range=insert_range,
            new_text=final_macro_xml,
        )

    def _edit_add_macro_to_macros_section(self, tool: GalaxyToolXmlDocument, macro: MacroData) -> TextEdit:
        """Returns the TextEdit operation that will add a macro definition to the <macros> section of a tool wrapper."""
        macros_element = tool.get_macros_element()
        insert_position = tool.get_position_after_last_child(macros_element)
        insert_range = Range(start=insert_position, end=insert_position)
        macro_xml = f'<xml name="{macro.name}">\n{macro.content}\n</xml>'
        final_macro_xml = self._adapt_format(tool.xml_document, insert_range, macro_xml)
        return TextEdit(
            range=insert_range,
            new_text=final_macro_xml,
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

    def _get_range_from_line_start(self, range: Range) -> Range:
        """Given an arbitrary document range, returns the same range but with the start offset always at the
        begining of the line."""
        return Range(start=Position(line=range.start.line, character=0), end=range.end)

    def _apply_indent(self, text: str, indent: str) -> str:
        """Applies the `indent` amount of spaces to all lines of the given text."""
        indented = indent + text.replace("\n", "\n" + indent)
        return indented

    def _adapt_format(
        self, xml_document: XmlDocument, insert_range: Range, xml_text: str, insert_in_new_line: bool = True
    ) -> str:
        """Adapts a chunk of XML text to the current formatting of the document given the insertion position."""
        formatted_macro = self.format_service.format_content(xml_text).rstrip()
        reference_line = insert_range.start.line
        if not insert_in_new_line:
            reference_line -= 1
        indent = xml_document.get_line_indentation(reference_line)
        final_macro_text = self._apply_indent(formatted_macro, indent)
        if insert_in_new_line:
            return f"\n{final_macro_text}"
        return final_macro_text


class RefactoringService:
    def __init__(self, macros_refactoring_service: RefactorMacrosService) -> None:
        self.macros = macros_refactoring_service

    def get_available_refactoring_actions(self, xml_document: XmlDocument, params: CodeActionParams) -> List[CodeAction]:
        """Gets a collection of possible refactoring code actions on a selected chunk of the document."""
        code_actions = []
        text_in_range = xml_document.get_text_in_range(params.range)
        target_element_tag = self._get_valid_full_element_tag(text_in_range)
        if target_element_tag is not None:
            macro = MacroData(name=target_element_tag, content=text_in_range.strip())
            macro_definitions = self.macros.definitions_provider.load_macro_definitions(xml_document)
            tool = GalaxyToolXmlDocument.from_xml_document(xml_document)
            code_actions.extend(self.macros.create_extract_to_macros_file_actions(tool, macro_definitions, macro, params))
            code_actions.extend(self.macros.create_extract_to_local_macro_actions(tool, macro, params))
        return code_actions

    def _get_valid_full_element_tag(self, xml_text: str) -> Optional[str]:
        """Given a chunk of XML text, returns the name of the tag inside it or None if the
        node is incomplete or sintactically wrong."""
        stripped_xml = xml_text.strip()
        if len(stripped_xml) < 5 or (stripped_xml[0] != "<" or stripped_xml[-1] != ">"):
            # Too short to be an element or doesn't look like an element
            return None
        return self._get_valid_node_tag(stripped_xml, EXCLUDED_TAGS)

    def _get_valid_node_tag(self, stripped_xml: str, exclude: Set[str]) -> Optional[str]:
        """Returns the name of the tag of a sintactically well formed xml text.

        The parameter `exclude` can define a set of tags that will be considered not valid."""
        try:
            xml_in_range = etree.fromstring(stripped_xml, etree.XMLParser(strip_cdata=False))
            if xml_in_range.tag not in exclude:
                return xml_in_range.tag
        except BaseException:
            pass  # Ignore, the xml chunk is not a valid xml node
        return None
