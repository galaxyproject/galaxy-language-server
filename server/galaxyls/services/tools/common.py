import abc
from typing import List, Optional

from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xml.nodes import XmlElement
from galaxyls.types import ReplaceTextRangeResult


class ToolParamAttributeSorter(metaclass=abc.ABCMeta):
    """Interface to sort attributes inside an element and return them as a document replace range edit.

    The sort criteria is defined by the implementing class.
    """

    @abc.abstractmethod
    def sort_param_attributes(self, param: XmlElement, xml_document: XmlDocument) -> Optional[ReplaceTextRangeResult]:
        """Returns a document replace edit with the sorted attributes of the given param contained in the xml_document."""
        raise NotImplementedError

    @abc.abstractmethod
    def sort_document_param_attributes(self, xml_document: XmlDocument) -> List[ReplaceTextRangeResult]:
        """Returns a collection of edits with all the attributes of the param elements in the document sorted."""
        raise NotImplementedError
