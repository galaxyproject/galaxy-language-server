from typing import Optional

from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.nodes import XmlElement
from galaxyls.types import ParamReferencesResult


class ParamReferencesProvider:
    def get_param_references(self, xml_document: XmlDocument) -> Optional[ParamReferencesResult]:
        tool = GalaxyToolXmlDocument.from_xml_document(xml_document).get_expanded_tool_document()
        references = []
        params = tool.get_input_params()
        for param in params:
            reference = self._build_reference(param)
            if reference:
                references.append(reference)

        return ParamReferencesResult(references)

    def _build_reference(self, param: XmlElement) -> Optional[str]:
        reference = None
        # The reference should be a string with the path to the param separated by dots and starting with a $
        # Skip the first 3 ancestors (document root, tool, inputs) to start at the input element.
        ancestors = param.ancestors[3:]
        path = []
        for ancestor in ancestors:
            name = ancestor.get_attribute_value("name")
            if name:
                path.append(name)
        name = self._get_param_name(param)
        if name:
            path.append(name)
        if path:
            reference = f"${'.'.join(path)}"
        return reference

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
