""" Type definitions for XSD processing.
"""

from anytree import NodeMixin, findall
from typing import List, Dict
from pygls.types import MarkupContent, MarkupKind
from .constants import MSG_NO_DOCUMENTATION_AVAILABLE


class XsdBase:
    """Base class that encapsulates an element from the XSD schema.

    It contains common information and functionality shared by
    XML nodes and attributes.
    """

    name: str

    def __init__(self, name: str, element):
        super(XsdBase, self).__init__()
        self.name = name
        self.xsd_element = element

    def get_doc(self, lang: str = "en") -> MarkupContent:
        """Gets the Markdown documentation associated with this element
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
            return MarkupContent(MarkupKind.Markdown, doc[0].strip())
        except BaseException:
            return MarkupContent(
                MarkupKind.Markdown, MSG_NO_DOCUMENTATION_AVAILABLE
            )


class XsdAttribute(XsdBase):
    """Represents an attribute in an XML tag.

    It contains information about the attribute extracted
    from the XSD schema.

    Args:
        XsdBase: Inherits base functionality from XsdBase.
    """

    type_name: str
    is_required: bool
    enumeration: List[str]

    def __init__(self, name, element, type_name, is_required):
        super(XsdAttribute, self).__init__(name, element)
        self.type_name = type_name
        self.is_required = is_required
        self.enumeration = []


class XsdNode(XsdBase, NodeMixin):
    """Represents a particular XML tag.

    The node contains information extracted from the XSD schema
    about the XML tag, possible descendants, attributes, etc.

    Args:
        XsdBase: Inherits base functionality from XsdBase.
        NodeMixin: Inherits tree node functionality from NodeMixin.
    """

    min_occurs: int
    max_occurs: int
    type_name: str
    attributes: Dict[str, XsdAttribute]

    def __init__(self, name, element, parent=None):
        super(XsdNode, self).__init__(name, element)
        self.parent = parent
        self.attributes = {}
        self.min_occurs = 1  # required by default
        self.max_occurs = -1  # unbounded by default


class XsdTree:
    """Represents a tree structure containing the important
    XSD information for all the elements and attributes.
    """

    root: XsdNode

    def __init__(self, root: XsdNode):
        self.root = root

    def find_node_by_name(self, name: str) -> XsdNode:
        """Finds node in the tree that matches the given name.

        Args:
            name (str): The name of the node to find.

        Returns:
            XsdNode: The node that matches the name or None if
            not found.
        """
        nodes = findall(self.root, lambda node: node.name == name)
        if len(nodes) == 0:
            return None
        return nodes[0]
