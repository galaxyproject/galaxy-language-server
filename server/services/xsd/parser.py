"""Module for converting XSD schema to tree structure
to simplify access to definitions.
"""

from lxml import etree
from .types import XmlElement, XmlAttribute

from .constants import (
    XS_ALL,
    XS_ATTRIBUTE,
    XS_COMPLEX_TYPE,
    XS_ELEMENT,
    XS_SEQUENCE,
    XS_SIMPLE_TYPE,
)


class XsdParser:
    """Parser for converting the XSD schema into a tree structure."""

    def __init__(self, xsd_root: etree.Element):
        """Initializes the parser with the given etree root element.

        Args:
            xsd_root (etree._Element): The root element of the XSD.
        """
        self._root = xsd_root
        self._tree = None
        self._named_type_map = {}

    def get_tree(self) -> XmlElement:
        if self._tree is None:
            self._register_named_types()
            self._build_tree_recursive(self._root, self._tree)
        return self._tree

    def _register_named_types(self):
        for element in self._root.findall(XS_COMPLEX_TYPE):
            name = element.get("name")
            self._named_type_map[name] = element

        for element in self._root.findall(XS_SIMPLE_TYPE):
            name = element.get("name")
            self._named_type_map[name] = element

    def _build_tree_recursive(self, parent_element, parent_node: XmlElement):
        for element in parent_element:
            tag = element.tag
            element_name = element.attrib.get("name")
            element_type_name = element.attrib.get("type")
            if tag == XS_ELEMENT:
                node = XmlElement(element_name, element, parent_node)
                if not parent_node:  # Is root element
                    self._tree = node
                node.type_name = element_type_name
                self._apply_named_type_to_node(element_type_name, node)
                # minOccurs defaults to 1
                node.min_occurs = int(element.attrib.get("minOccurs", 1))
                self._build_tree_recursive(element, node)

            elif tag == XS_COMPLEX_TYPE:
                if not element_name:
                    # The type has no name and is declared inside the element
                    # so we can directly apply it to the node
                    self._apply_complex_type_to_node(element, parent_node)

    def _apply_named_type_to_node(self, type_name, node: XmlElement):
        element_type = self._named_type_map.get(type_name, None)
        if element_type is None:
            return
        if element_type.tag == XS_COMPLEX_TYPE:
            self._apply_complex_type_to_node(element_type, node)
        else:
            self._apply_simple_type_to_node(element_type, node)

    def _apply_complex_type_to_node(self, complex_type, node: XmlElement):
        for child_element in complex_type:
            tag = child_element.tag
            if tag == XS_ALL or tag == XS_SEQUENCE:
                self._build_tree_recursive(child_element, node)
            elif tag == XS_ATTRIBUTE:
                self._add_attribute_to_node(child_element, node)

    def _apply_simple_type_to_node(self, simple_type, node: XmlElement):
        # TODO
        pass

    def _add_attribute_to_node(self, attribute_element, node: XmlElement):
        attr_name = attribute_element.attrib.get("name")
        attr_type = attribute_element.attrib.get("type")
        attr_use = attribute_element.attrib.get("use")
        attr = XmlAttribute(
            attr_name, attribute_element, attr_type, attr_use == "required"
        )
        node.attributes.append(attr)
