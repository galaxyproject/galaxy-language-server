from typing import List, Optional

from galaxyls.services.tools.common import ToolParamAttributeSorter
from galaxyls.services.tools.constants import (
    ARGUMENT,
    CHECKED,
    FALSEVALUE,
    FORMAT,
    HELP,
    LABEL,
    MAX,
    MIN,
    NAME,
    OPTIONAL,
    PARAM,
    TRUEVALUE,
    TYPE,
    VALUE,
)
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.nodes import XmlAttribute, XmlElement
from galaxyls.services.xml.utils import convert_document_offsets_to_range
from galaxyls.types import ReplaceTextRangeResult

ORDER_LAST = 100


class IUCToolParamAttributeSorter(ToolParamAttributeSorter):
    IUC_PARAM_ATTR_ORDER = {
        NAME: 0,
        ARGUMENT: 1,
        TYPE: 2,
        FORMAT: 3,
        MIN: 4,
        MAX: 5,
        VALUE: 6,
        TRUEVALUE: 4,
        FALSEVALUE: 5,
        CHECKED: 6,
        OPTIONAL: 7,
        LABEL: 8,
        HELP: 9,
    }

    def sort_param_attributes(self, param: XmlElement, xml_document: XmlDocument) -> Optional[ReplaceTextRangeResult]:
        if param and param.name == PARAM and param.has_attributes:
            attribute_names = param.get_attribute_names()
            sorted_attribute_names = self._sort_attribute_names(attribute_names)
            if attribute_names == sorted_attribute_names:
                return None
            sorted_attributes_text = self._get_param_attributes_as_text_sorted(param, sorted_attribute_names)
            start, end = param.get_attributes_offsets()
            return ReplaceTextRangeResult(
                replace_range=convert_document_offsets_to_range(xml_document.document, start, end),
                text=sorted_attributes_text,
            )
        return None

    def sort_document_param_attributes(self, xml_document: XmlDocument) -> List[ReplaceTextRangeResult]:
        params = xml_document.find_all_elements_with_name(PARAM)
        rval: List[ReplaceTextRangeResult] = []
        for param in params:
            result = self.sort_param_attributes(param, xml_document)
            if result:
                rval.append(result)
        return rval

    def _sort_attribute_names(self, attributes: List[str]) -> List[str]:
        return sorted(attributes, key=lambda attr: self._get_attr_order(attr))

    def _get_attr_order(self, attr_name: str) -> int:
        return self.IUC_PARAM_ATTR_ORDER.get(attr_name, ORDER_LAST)

    def _get_param_attributes_as_text_sorted(self, element: XmlElement, sorted_attr_names: List[str]) -> str:
        printed_attributes = [self._attr_to_text(element.attributes[attr_name]) for attr_name in sorted_attr_names]
        return " ".join(printed_attributes)

    def _attr_to_text(self, attr: XmlAttribute) -> str:
        if attr and attr.name and attr.value:
            return f'{attr.name}="{attr.get_value()}"'
        return ""
