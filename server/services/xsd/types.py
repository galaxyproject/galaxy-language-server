""" Type definitions for XSD processing.
"""

from anytree import NodeMixin
from typing import List
from .constants import MSG_NO_DOCUMENTATION_AVAILABLE


class XmlBase:
    name: str

    def __init__(self, name: str, element):
        super(XmlBase, self).__init__()
        self.name = name
        self.xsd_element = element

    def get_doc(self, lang: str = "en") -> str:
        """Gets the documentation associated with this element
        from the XSD schema.

        If there is no documentation in the schema for the element,
        a message indicating this will be returned instead.

        Args:
            lang (str, optional): The language code of the documentation
            to retrieve. Defaults to "en" (English).

        Returns:
            [str]: The documentation text or a message indicating
            there is no documentation.
        """
        try:
            doc = self.xsd_element.xpath(
                "./xs:annotation/xs:documentation[@xml:lang=$lang]/text()",
                namespaces=self.xsd_element.nsmap,
                lang=lang,
            )
            return doc[0].strip()
        except BaseException:
            return MSG_NO_DOCUMENTATION_AVAILABLE


class XmlAttribute(XmlBase):
    type_name: str
    is_required: bool

    def __init__(self, name, element, type_name, is_required):
        super(XmlAttribute, self).__init__(name, element)
        self.type_name = type_name
        self.is_required = is_required


class XmlElement(XmlBase, NodeMixin):
    attributes: List[XmlAttribute]
    min_occurs: int
    max_occurs: int
    type_name: str

    def __init__(self, name, element, parent=None):
        super(XmlElement, self).__init__(name, element)
        self.parent = parent
        self.attributes = []
        self.min_occurs = 1  # required by default
        self.max_occurs = -1  # unbounded by default
