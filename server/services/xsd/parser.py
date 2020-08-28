"""Module for converting XSD schema to tree structure
to simplify access to definitions.
"""

from lxml import etree
from typing import List, Optional
from .types import XsdNode, XsdAttribute, XsdTree

from .constants import (
    XS_ALL,
    XS_ATTRIBUTE,
    XS_COMPLEX_TYPE,
    XS_ELEMENT,
    XS_SEQUENCE,
    XS_SIMPLE_TYPE,
)


class XsdParser:
    """Parser for converting the XSD schema into a tree structure
    that it is easy to use to retrieve information about the schema.

    Note: the conversion is focused in supporting the elements and types
    used in the Galaxy tool's XSD and not all the possible definitions
    supported by the XSD specification.
    """

    def __init__(self, xsd_root: etree.Element):
        """Initializes the parser with the given etree root element.

        Args:
            xsd_root (etree.Element): The root element of the XSD.
        """
        self._root = xsd_root
        self._tree = None
        self._named_type_map = {}

    def get_tree(self) -> XsdTree:
        """Builds the tree structure from the root etree.Element if
        it does not exists, or returns it if exists.

        Returns:
            XsdTree: The tree structure with all the relevan
            information from the XSD schema.
        """
        if self._tree is None:
            self._register_named_types()
            self._build_tree_recursive(self._root, self._tree)
        return self._tree

    def _register_named_types(self):
        """Finds all (named) complex and simple type definitions in the
        XSD schema and register them in a dictionary.
        """
        for element in self._root.findall(XS_COMPLEX_TYPE):
            name = element.get("name")
            self._named_type_map[name] = element

        for element in self._root.findall(XS_SIMPLE_TYPE):
            name = element.get("name")
            self._named_type_map[name] = element

    def _build_tree_recursive(
        self, parent_element: etree.Element, parent_node: XsdNode
    ):
        for element in parent_element:
            tag = element.tag
            element_name = element.attrib.get("name")
            element_type_name = element.attrib.get("type")
            if tag == XS_ELEMENT:
                node = XsdNode(element_name, element, parent_node)
                if not parent_node:  # Is root element
                    self._tree = XsdTree(node)
                node.type_name = element_type_name
                self._apply_named_type_to_node(element_type_name, node)
                # minOccurs defaults to 1
                node.min_occurs = int(element.attrib.get("minOccurs", 1))
                self._build_tree_recursive(element, node)

            elif tag == XS_COMPLEX_TYPE:
                if not element_name:
                    # The type is anonymous and is declared inside the element
                    # so we can directly apply it to the node
                    self._apply_complex_type_to_node(element, parent_node)

    def _apply_named_type_to_node(self, type_name: str, node: XsdNode):
        element_type = self._named_type_map.get(type_name, None)
        if element_type is None:
            return
        if element_type.tag == XS_COMPLEX_TYPE:
            self._apply_complex_type_to_node(element_type, node)

    def _apply_complex_type_to_node(
        self, complex_type: etree.Element, node: XsdNode
    ):
        for child_element in complex_type:
            tag = child_element.tag
            if tag == XS_ALL or tag == XS_SEQUENCE:
                self._build_tree_recursive(child_element, node)
            elif tag == XS_ATTRIBUTE:
                self._add_attribute_to_node(child_element, node)

    def _add_attribute_to_node(
        self, attribute_element: etree.Element, node: XsdNode
    ):
        attr_name = attribute_element.attrib.get("name")
        attr_type = attribute_element.attrib.get("type")
        attr_use = attribute_element.attrib.get("use")
        attr = XsdAttribute(
            attr_name, attribute_element, attr_type, attr_use == "required"
        )
        attr.enumeration = self._get_enumeration_restrictions_from_type(
            attr_type
        )
        node.attributes[attr_name] = attr

    def _get_enumeration_restrictions_from_type(
        self, type_name: str
    ) -> Optional[List[str]]:
        simple_type = self._named_type_map.get(type_name, None)
        if simple_type is None:
            return []
        if simple_type.tag == XS_SIMPLE_TYPE:
            return simple_type.xpath(
                ".//xs:enumeration/@value", namespaces=simple_type.nsmap
            )
