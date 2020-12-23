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
from galaxyls.services.tools.inputs import (
    ConditionalInputNode,
    GalaxyToolInputTree,
    InputNode,
    RepeatInputNode,
    SectionInputNode,
)
from galaxyls.services.xml.nodes import XmlElement
from pygls.types import Position

ARG_PLACEHOLDER = "TODO_argument"
REPEAT_VAR = "var"
REPEAT_INDEX = "i"


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
            "\n## Inputs\n",
        ]
        for node in PreOrderIter(input_tree._root):
            node = cast(InputNode, node)
            if type(node) is ConditionalInputNode:
                indentation_level = node.depth - 1
                result = self._conditional_to_cheetah(node, indentation_level)
                snippets.extend(result)
            else:
                result = self._node_to_cheetah(node)
                snippets.extend(result)

        snippets.append("\n## Outputs\n")
        for output in outputs:
            variable = self._output_to_cheetah(output)
            if variable:
                snippets.append(variable)
        return "\n".join(snippets)

    def _param_to_cheetah(self, input: XmlElement, parent_name: Optional[str] = None, indent_level: int = 0) -> str:
        indentation = self._get_indentation(indent_level)
        argument_attr = input.get_attribute(ARGUMENT)
        name_attr = input.get_attribute(NAME)
        if not name_attr and argument_attr:
            name_attr = argument_attr.lstrip(DASH).replace(DASH, UNDERSCORE)
        type_attr = input.get_attribute(TYPE)
        if parent_name:
            name_attr = f"{parent_name}.{name_attr}"
        if type_attr == BOOLEAN:
            return f"{indentation}\\${input.get_attribute(TRUEVALUE) or name_attr}"
        if type_attr in [INTEGER, FLOAT]:
            if input.get_attribute(OPTIONAL) == "true":
                return (
                    f"{indentation}#if str(\\${name_attr}):\n"
                    f"{indentation}{self.indent_spaces}{self._get_argument_safe(argument_attr)} \\${name_attr}"
                    f"{indentation}#end if"
                )
        if type_attr in [TEXT, DATA]:
            return f"{indentation}{self._get_argument_safe(argument_attr)} '\\${name_attr}'"
        return f"{indentation}{self._get_argument_safe(argument_attr)} \\${name_attr}"

    def _node_to_cheetah(self, node: InputNode, parent_name: Optional[str] = None, indent_level: int = 0) -> List[str]:
        result: List[str] = []
        for param in node.params:
            result.append(self._param_to_cheetah(param, parent_name, indent_level))
        for repeat in node.repeats:
            result.extend(self._repeat_to_cheetah(repeat, indent_level))
        for section in node.sections:
            result.extend(self._section_to_cheetah(section, indent_level))
        return result

    def _conditional_to_cheetah(self, conditional: ConditionalInputNode, indent_level: int = 0) -> List[str]:
        indentation = self._get_indentation(indent_level)
        result: List[str] = []
        cond_name = conditional.name
        param_name = conditional.option_param.get_attribute(NAME)
        option = conditional.option
        directive = "#elif"
        if conditional.is_first_option:
            directive = "#if"
        result.append(f'{indentation}{directive} str( \\${cond_name}.{param_name} ) == "{option}":')
        result.extend(self._node_to_cheetah(conditional, cond_name, indent_level + 1))
        if conditional.is_last_option:
            result.append(f"{indentation}#end if")
        return result

    def _repeat_to_cheetah(self, repeat: RepeatInputNode, indent_level: int = 0) -> List[str]:
        indentation = self._get_indentation(indent_level)
        result: List[str] = []
        repeat_name = repeat.element.get_attribute(NAME)
        result.append(f"{indentation}#for \\${REPEAT_INDEX}, \\${REPEAT_VAR} in enumerate(\\${repeat_name}):")
        result.extend(self._node_to_cheetah(repeat, REPEAT_VAR, indent_level + 1))
        result.append(f"{indentation}#end for")
        return result

    def _section_to_cheetah(self, section: SectionInputNode, indent_level: int = 0) -> List[str]:
        result: List[str] = []
        section_name = section.element.get_attribute(NAME)
        result.extend(self._node_to_cheetah(section, section_name, indent_level))
        return result

    def _output_to_cheetah(self, output: XmlElement) -> Optional[str]:
        name = output.get_attribute(NAME)
        if name:
            return f"\\${name}"
        return None

    def _get_argument_safe(self, argument: Optional[str]) -> str:
        return argument or self._get_next_tabstop_with_placeholder(ARG_PLACEHOLDER)

    def _get_indentation(self, level: int) -> str:
        return self.indent_spaces * level
