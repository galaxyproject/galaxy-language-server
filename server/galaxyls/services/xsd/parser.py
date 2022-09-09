"""Module for converting XSD schema to tree structure
to simplify access to definitions.
"""

from typing import (
    cast,
    Dict,
    List,
    Optional,
)

from lxml import etree

from .constants import (
    MAX_RECURSION_DEPTH,
    XS_ALL,
    XS_ATTRIBUTE,
    XS_ATTRIBUTE_GROUP,
    XS_CHOICE,
    XS_COMPLEX_CONTENT,
    XS_COMPLEX_TYPE,
    XS_ELEMENT,
    XS_EXTENSION,
    XS_GROUP,
    XS_SEQUENCE,
    XS_SIMPLE_CONTENT,
    XS_SIMPLE_TYPE,
)
from .types import (
    XsdAttribute,
    XsdNode,
    XsdTree,
)


class GalaxyToolXsdParser:
    """Parser for converting the XSD schema into a tree structure
    that it is easy to use to retrieve information about the schema.

    Note: the conversion is focused in supporting the definitions
    used in the Galaxy tool's XSD and not all the possible definitions
    supported by the XSD specification.
    """

    def __init__(self, xsd_root: etree._Element):
        """Initializes the parser with the given etree root element.

        Args:
            xsd_root (etree._Element): The root element of the XSD.
        """
        self._root: etree._Element = xsd_root
        self._tree: Optional[XsdTree] = None
        self._named_type_map: Dict[str, etree._Element] = {}
        self._named_group_map: Dict[str, etree._Element] = {}

    def get_tree(self) -> XsdTree:
        """Builds the tree structure from the root etree._Element if
        it does not exists, or returns it if exists.

        Returns:
            XsdTree: The tree structure with all the relevant
            information from the XSD schema.
        """
        if self._tree is None:
            self._register_named_types()
            self._register_named_groups()
            self._build_tree_recursive(self._root, self._tree)
            if self._tree is None:
                self._tree = self._build_empty_tree()
        return self._tree

    def _build_empty_tree(self) -> XsdTree:
        return XsdTree(XsdNode(""))

    def _register_named_types(self) -> None:
        """Finds all (named) complex and simple type definitions in the
        XSD schema and register them in a dictionary.
        """
        for element in self._root.findall(XS_COMPLEX_TYPE):
            name = element.get("name")
            if name:
                self._named_type_map[name] = element

        for element in self._root.findall(XS_SIMPLE_TYPE):
            name = element.get("name")
            if name:
                self._named_type_map[name] = element

    def _register_named_groups(self) -> None:
        """Finds all (named) groups and attribute group definitions in the
        XSD schema and register them in a dictionary.
        """
        for element in self._root.findall(XS_GROUP):
            name = element.get("name")
            if name:
                self._named_group_map[name] = element

        for element in self._root.findall(XS_ATTRIBUTE_GROUP):
            name = element.get("name")
            if name:
                self._named_group_map[name] = element

    def _build_tree_recursive(self, parent_element: etree._Element, parent_node: Optional[XsdNode], depth: int = 0) -> None:
        if depth > MAX_RECURSION_DEPTH:
            return None  # Stop recursion

        for element in parent_element:
            tag = element.tag
            element_name = cast(Optional[str], element.attrib.get("name"))
            element_type_name = self._get_attribute_value_by_name(element, "type")
            if tag == XS_ELEMENT and element_name is not None:
                node = XsdNode(element_name, element, parent_node)
                if not parent_node:  # Is root element
                    self._tree = XsdTree(node)
                node.xsd_type = self._named_type_map.get(element_type_name)
                self._apply_named_type_to_node(element_type_name, node, depth + 1)
                # minOccurs defaults to 1
                min_occurs = cast(str, element.attrib.get("minOccurs", "1"))
                node.min_occurs = int(min_occurs)
                max_occurs = cast(str, element.attrib.get("maxOccurs", "unbounded"))
                node.max_occurs = int(max_occurs) if max_occurs != "unbounded" else -1
                self._build_tree_recursive(element, node, depth + 1)
            elif tag == XS_COMPLEX_TYPE:
                if not element_name and parent_node:
                    # The type is anonymous and is declared inside the element
                    # so we can directly apply it to the node
                    self._apply_complex_type_to_node(element, parent_node, depth + 1)
            elif tag == XS_GROUP:
                element_ref = cast(Optional[str], element.attrib.get("ref"))
                if element_ref and parent_node:
                    self._apply_group_to_node(element_ref, parent_node, depth + 1)

    def _apply_named_type_to_node(self, type_name: str, node: XsdNode, depth: int = 0) -> None:
        element_type = self._named_type_map.get(type_name)
        if element_type is not None and element_type.tag == XS_COMPLEX_TYPE:
            self._apply_complex_type_to_node(element_type, node, depth + 1)

    def _apply_complex_type_to_node(self, complex_type: etree._Element, node: XsdNode, depth: int = 0) -> None:
        for child_element in complex_type:
            tag = child_element.tag
            if tag in [XS_ALL, XS_SEQUENCE, XS_CHOICE]:
                self._build_tree_recursive(child_element, node, depth + 1)
            elif tag == XS_ATTRIBUTE:
                self._add_attribute_to_node(child_element, node)
            elif tag == XS_ATTRIBUTE_GROUP:
                element_ref = cast(Optional[str], child_element.attrib.get("ref"))
                if element_ref:
                    self._apply_attribute_group_to_node(element_ref, node)
            elif tag == XS_SIMPLE_CONTENT:
                self._apply_simple_content_to_node(child_element, node)
            elif tag == XS_COMPLEX_CONTENT:
                self._apply_complex_content_to_node(child_element, node, depth)

    def _apply_attribute_group_to_node(self, group_name: str, node: XsdNode) -> None:
        group = self._named_group_map.get(group_name)
        if group is not None:
            for child_element in group:
                self._add_attribute_to_node(child_element, node)

    def _apply_group_to_node(
        self,
        group_name: str,
        node: XsdNode,
        depth: int,
    ) -> None:
        group = self._named_group_map.get(group_name)
        if group is not None:
            for child_element in group:
                self._build_tree_recursive(child_element, node, depth + 1)

    def _apply_simple_content_to_node(self, simple_content: etree._Element, node: XsdNode) -> None:
        for child_elem in simple_content:
            if child_elem.tag == XS_EXTENSION:
                attributes = child_elem.findall(XS_ATTRIBUTE)
                for attr_elem in attributes:
                    self._add_attribute_to_node(attr_elem, node)

    def _apply_complex_content_to_node(self, complex_content: etree._Element, node: XsdNode, depth: int) -> None:
        for child_elem in complex_content:
            if child_elem.tag == XS_EXTENSION:
                attr_base = self._get_attribute_value_by_name(child_elem, "base")
                if attr_base:
                    self._apply_named_type_to_node(attr_base, node, depth)
                self._apply_complex_type_to_node(child_elem, node, depth)

    def _add_attribute_to_node(self, attribute_element: etree._Element, node: XsdNode) -> None:
        attr_name = self._get_attribute_value_by_name(attribute_element, "name")
        attr_type = self._get_attribute_value_by_name(attribute_element, "type")
        attr_use = self._get_attribute_value_by_name(attribute_element, "use")
        attr = XsdAttribute(attr_name, attribute_element, attr_type, attr_use == "required")
        attr.enumeration = self._get_enumeration_restrictions_from_type(attr_type)
        node.attributes[attr_name] = attr

    def _get_enumeration_restrictions_from_type(self, type_name: str) -> List[str]:
        simple_type = self._named_type_map.get(type_name)
        if simple_type is not None and simple_type.tag == XS_SIMPLE_TYPE:
            enumeration_values = simple_type.xpath(".//xs:enumeration/@value", namespaces=simple_type.nsmap)  # type: ignore
            return cast(List[str], enumeration_values)
        return []

    def _get_attribute_value_by_name(self, element: etree._Element, name: str) -> str:
        return cast(str, element.attrib.get(name, ""))
