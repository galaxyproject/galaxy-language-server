""" Type definitions for XSD processing.
"""

from anytree import NodeMixin
from typing import List
from .constants import XS_NAMESPACE


class XmlBase:
    name: str

    def __init__(self, name, element):
        super(XmlBase, self).__init__()
        self.name = name
        self.xsd_element = element

    def get_doc(self):
        try:
            doc = self.xsd_element.find(
                ".//xs:annotation/xs:documentation/text()",
                namespaces={"xs": XS_NAMESPACE},
            )
            return doc
        except BaseException:
            return "No documentation available"


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

    def __init__(self, name, element, parent=None, children=None):
        super(XmlElement, self).__init__(name, element)
        self.parent = parent
        self.attributes = []
        if children:  # set children only if given
            self.children = children
