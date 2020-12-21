from typing import List, Optional, cast

from anytree import PreOrderIter
from galaxyls.services.tools.constants import (
    ARGUMENT,
    BOOLEAN,
    COMMAND,
    CONFIGFILES,
    DASH,
    DATA,
    ENV_VARIABLES,
    FLOAT,
    INPUTS,
    INTEGER,
    NAME,
    OPTIONAL,
    TEXT,
    TRUEVALUE,
    TYPE,
    UNDERSCORE,
)
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.tools.generators.snippets import SnippetGenerator
from galaxyls.services.tools.inputs import ConditionalInputNode, GalaxyToolInputTree, InputNode
from galaxyls.services.xml.nodes import XmlElement
from pygls.types import Position

ARG_PLACEHOLDER = "TODO_argument"


class GalaxyToolCommandSnippetGenerator(SnippetGenerator):
    """This class tries to generate some boilerplate Cheetah code for the command
    section using the information already defined in the inputs and outputs of the tool XML wrapper.
    """

    def __init__(self, tool_document: GalaxyToolXmlDocument, tabSize: int = 4) -> None:
        super().__init__(tool_document, tabSize)

    def _build_snippet(self) -> Optional[str]:
        input_tree = self.tool_document.analyze_inputs()
        outputs = self.tool_document.get_outputs()
        result_snippet = self._generate_command_snippet(input_tree, outputs)
        create_section = not self.tool_document.has_section_content(COMMAND)
        if create_section:
            return f"<{COMMAND}><![CDATA[\n\n{result_snippet}\n\n]]>\n</{COMMAND}>\n"
        return result_snippet

    def _find_snippet_insert_position(self) -> Position:
        """Returns the position inside the document where command section
        can be inserted.

        If the <command> section does not exists in the file, the best aproximate
        position where the section should be inserted is returned (acording to the IUC
        best practices tag order).

        Returns:
            Position: The position where the command section can be inserted in the document.
        """
        tool = self.tool_document
        section = tool.find_element(COMMAND)
        if section:
            content_range = tool.get_element_content_range(section)
            if content_range:
                return content_range.end
            else:  # is self closed <tests/>
                return tool.get_position_before(section)
        else:
            section = tool.find_element(ENV_VARIABLES)
            if section:
                return tool.get_position_before(section)
            section = tool.find_element(CONFIGFILES)
            if section:
                return tool.get_position_before(section)
            section = tool.find_element(INPUTS)
            if section:
                return tool.get_position_before(section)
            return Position()

    def _generate_command_snippet(self, input_tree: GalaxyToolInputTree, outputs: List[XmlElement]) -> str:
        snippets = [
            "## Auto-generated command section",
            "## TODO: please review and edit this section as needed",
            "\n## Inputs",
        ]
        for node in PreOrderIter(input_tree._root):
            node = cast(InputNode, node)
            if type(node) is ConditionalInputNode:
                pass
            else:
                for param in node.params:
                    snippets.append(self._input_to_cheetah(param))
        snippets.append("\n## Outputs\n")
        return "\n".join(snippets)

    def _input_to_cheetah(self, input: XmlElement) -> str:
        argument_attr = input.get_attribute(ARGUMENT)
        name_attr = input.get_attribute(NAME)
        if not name_attr and argument_attr:
            name_attr = argument_attr.lstrip(DASH).replace(DASH, UNDERSCORE)
        type_attr = input.get_attribute(TYPE)
        if type_attr == BOOLEAN:
            return f"\\${input.get_attribute(TRUEVALUE) or name_attr}"
        if type_attr in [INTEGER, FLOAT]:
            if input.get_attribute(OPTIONAL) == "true":
                return (
                    f"#if str(\\${name_attr}):\n"
                    f"{self.indent_spaces}{self._get_argument_safe(argument_attr)} \\${name_attr}"
                    f"#end if"
                )
        if type_attr in [TEXT, DATA]:
            return f"{self._get_argument_safe(argument_attr)} '\\${name_attr}'"
        return f"{self._get_argument_safe(argument_attr)} \\${name_attr}"

    def _get_argument_safe(self, argument: Optional[str]) -> str:
        return argument or self._get_next_tabstop_with_placeholder(ARG_PLACEHOLDER)
