from typing import List, Optional

from galaxyls.services.tools.constants import COMMAND, CONFIGFILES, ENV_VARIABLES, INPUTS
from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.tools.generators.snippets import SnippetGenerator
from galaxyls.services.tools.inputs import GalaxyToolInputTree
from galaxyls.services.xml.nodes import XmlElement
from pygls.types import Position


class GalaxyToolCommandSnippetGenerator(SnippetGenerator):
    """This class tries to generate some boilerplate Cheetah code for the command
    section using the information already defined in the inputs and outputs of the tool XML wrapper.
    """

    def __init__(self, tool_document: GalaxyToolXmlDocument) -> None:
        super().__init__(tool_document)

    def _build_snippet(self, tabSize: int = 4) -> Optional[str]:
        spaces = " " * tabSize
        input_tree = self.tool_document.analyze_inputs()
        outputs = self.tool_document.get_outputs()
        result_snippet = self._generate_command_snippet(input_tree, outputs, spaces)
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

    def _generate_command_snippet(self, input_tree: GalaxyToolInputTree, outputs: List[XmlElement], spaces: str = "  ") -> str:
        return "## TODO Insert some cheetah code"
