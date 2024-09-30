from typing import List, Optional

from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.nodes import XmlElement
from galaxyls.types import ParamReferencesResult


class ParamReferencesProvider:
    def get_param_references(self, xml_document: XmlDocument) -> Optional[ParamReferencesResult]:
        """Returns a list of references for the input parameters of the tool that can be used in the command section."""
        tool = GalaxyToolXmlDocument.from_xml_document(xml_document).get_expanded_tool_document()
        references = []
        params = tool.get_input_params()
        for param in params:
            reference = self._build_reference(param)
            if reference:
                references.append(reference)
        return ParamReferencesResult(references)

    def get_param_path(self, param: XmlElement) -> List[str]:
        path = []
        # Skip the first 3 ancestors (document root, tool, inputs) to start at the input element.
        ancestors = param.ancestors[3:]
        for ancestor in ancestors:
            name = ancestor.get_attribute_value("name")
            if name:
                path.append(name)
        name = self._get_param_name(param)
        if name:
            path.append(name)
        return path

    def _get_param_name(self, param: XmlElement) -> Optional[str]:
        name = param.get_attribute_value("name")
        if not name:
            name = param.get_attribute_value("argument")
            if name:
                return self._normalize_argument_name(name)
        return name

    def _normalize_argument_name(self, argument: str) -> str:
        if argument.startswith("--"):
            argument = argument[2:]
        return argument.replace("-", "_")

    def _build_reference(self, param: XmlElement) -> Optional[str]:
        reference = None
        path = self.get_param_path(param)
        if path:
            reference = f"${'.'.join(path)}"
        return reference
