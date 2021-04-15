from typing import cast

from galaxy.util import xml_macros
from galaxyls.types import GeneratedExpandedDocument
from lxml import etree


def remove_macros(xml_tree: etree._ElementTree) -> etree._ElementTree:
    """Removes the macros section from the tool tree.

    Args:
        xml_tree (etree._ElementTree): The tool element tree.

    Returns:
        etree.ElementTree: The tool element tree without the macros section.
    """
    to_remove = []
    for macros_el in xml_tree.getroot().findall("macros"):
        to_remove.append(macros_el)
    for macros_el in to_remove:
        xml_tree.getroot().remove(macros_el)
    return xml_tree


class MacroExpanderService:
    def generate_expanded_from(self, tool_path: str) -> GeneratedExpandedDocument:
        result = GeneratedExpandedDocument()
        try:
            expanded_tool_tree, _ = xml_macros.load_with_references(tool_path)
            expanded_xml = remove_macros(expanded_tool_tree)
            root = expanded_xml.getroot()
            etree.indent(root, space=" " * 4)
            content = cast(str, etree.tostring(root, pretty_print=True, encoding=str))
            result.content = content
        except BaseException as e:
            result.error_message = f"{e}"
        return result
