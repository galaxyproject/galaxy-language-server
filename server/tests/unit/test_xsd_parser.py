import pytest

from lxml import etree
from ...services.xsd.parser import GalaxyToolXsdParser
from ...services.xsd.constants import MSG_NO_DOCUMENTATION_AVAILABLE

TEST_XSD = """<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="testElement" type="CustomComplexType">
    <xs:annotation>
      <xs:documentation xml:lang="en">
        <![CDATA[Documentation ``example``.]]>
      </xs:documentation>
      <xs:documentation xml:lang="es">
        <![CDATA[``Ejemplo`` de documentación.]]>
      </xs:documentation>
    </xs:annotation>
  </xs:element>
  <xs:complexType name="CustomComplexType">
    <xs:sequence>
      <xs:element name="firstElement" type="CustomIntSimpleType">
        <xs:annotation>
          <xs:documentation xml:lang="en">
            <![CDATA[
              This is a multiline
              documentation example.
            ]]>
          </xs:documentation>
        </xs:annotation>
      </xs:element>
      <xs:element name="secondElement" type="TestComplexContent"/>
      <xs:element name="thirdElement">
        <xs:complexType>
          <xs:sequence>
            <xs:element name="childElement" type="TestSimpleContent"/>
          </xs:sequence>
          <xs:attribute name="testDate" type="xs:date"/>
        </xs:complexType>
      </xs:element>
      <xs:element name="element_with_group" type="ComplexWithGroup"/>
    </xs:sequence>
    <xs:attribute name="id" type="xs:integer" use="required"/>
    <xs:attribute name="value" type="ValueSimpleType"/>
    <xs:attributeGroup ref="TestAttrGroup"/>
  </xs:complexType>
  <xs:complexType name="ComplexWithGroup">
    <xs:sequence>
      <xs:group ref="TestGroup" minOccurs="0" maxOccurs="1"/>
    </xs:sequence>
    <xs:attribute name="group_id" type="xs:integer"/>
  </xs:complexType>
  <xs:complexType name="TestSimpleContent">
    <xs:simpleContent>
      <xs:extension base="xs:string">
        <xs:attribute name="simple" type="ValueSimpleType" use="required"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="TestComplexContent">
    <xs:complexContent>
      <xs:extension base="ComplexWithGroup">
        <xs:sequence>
          <xs:element name="content" type="xs:string"/>
        </xs:sequence>
        <xs:attribute name="complex" type="xs:string"/>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:simpleType name="CustomIntSimpleType">
    <xs:restriction base="xs:integer">
      <xs:minInclusive value="1"/>
      <xs:maxInclusive value="30"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="ValueSimpleType">
    <xs:restriction base="xs:string">
        <xs:enumeration value="v1"/>
        <xs:enumeration value="v2"/>
        <xs:enumeration value="v3"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:attributeGroup name="TestAttrGroup">
    <xs:attribute name="gattr1" type="xs:string"/>
    <xs:attribute name="gattr2" type="xs:string"/>
  </xs:attributeGroup>
  <xs:group name="TestGroup">
    <xs:sequence>
      <xs:element name="group_elem1" type="xs:string"/>
      <xs:element name="group_elem2" type="xs:string"/>
    </xs:sequence>
  </xs:group>
</xs:schema>
"""
# Resulting XML tree for quick visual reference
# Please update it if the XSD above is modified:
#   print(tree.render())
"""
[testElement] id value gattr1 gattr2
├── [firstElement]
├── [secondElement] group_id complex
│   ├── [group_elem1]
│   ├── [group_elem2]
│   └── [content]
├── [thirdElement] testDate
│   └── [childElement] simple
└── [element_with_group] group_id
    ├── [group_elem1]
    └── [group_elem2]
"""

RECURSIVE_XSD = """<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="node" type="nodeType"/>
  <xs:complexType name="nodeType">
    <xs:sequence>
      <xs:element name="node" type="nodeType"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
"""


@pytest.fixture(scope="module")
def xsd_parser() -> GalaxyToolXsdParser:
    root = etree.fromstring(TEST_XSD)
    parser = GalaxyToolXsdParser(root)
    return parser


@pytest.fixture(scope="module")
def recursive_xsd_parser() -> GalaxyToolXsdParser:
    root = etree.fromstring(RECURSIVE_XSD)
    parser = GalaxyToolXsdParser(root)
    return parser


class TestXsdParserClass:
    def test_get_tree_returns_valid_element_names(self, xsd_parser):
        tree = xsd_parser.get_tree()
        root = tree.root

        # If the test fails the tree will be printed
        print(tree.render())

        assert len(root.ancestors) == 0
        assert len(root.descendants) == 10
        assert root.name == "testElement"
        assert root.children[0].name == "firstElement"
        assert root.children[1].name == "secondElement"
        assert root.children[1].children[0].name == "group_elem1"
        assert root.children[1].children[1].name == "group_elem2"
        assert root.children[1].children[2].name == "content"
        assert root.children[2].name == "thirdElement"
        assert root.children[2].children[0].name == "childElement"
        assert root.children[3].name == "element_with_group"
        assert root.children[3].children[0].name == "group_elem1"
        assert root.children[3].children[1].name == "group_elem2"

    def test_get_tree_returns_valid_attribute_names_using_groups(
        self, xsd_parser
    ):
        tree = xsd_parser.get_tree()
        root = tree.root

        assert len(root.attributes) == 4
        assert root.attributes["id"]
        assert root.attributes["value"]
        assert root.attributes["gattr1"]
        assert root.attributes["gattr2"]

    def test_get_tree_returns_valid_attribute_names_when_simple_content(
        self, xsd_parser
    ):
        tree = xsd_parser.get_tree()
        simple_content_elem = tree.root.children[2].children[0]

        assert len(simple_content_elem.attributes) == 1
        assert simple_content_elem.attributes["simple"]

    def test_get_tree_returns_valid_element_when_complex_content(
        self, xsd_parser
    ):
        tree = xsd_parser.get_tree()
        complex_content_elem = tree.root.children[2].children[0]

        assert len(complex_content_elem.attributes) == 1
        assert complex_content_elem.attributes["simple"]

    def test_get_tree_with_recursive_xsd_stops_recursion(
        self, recursive_xsd_parser
    ):
        tree = recursive_xsd_parser.get_tree()

        assert len(tree.root.descendants) > 0

    def test_tree_find_node_by_name_returns_expected_node(self, xsd_parser):
        tree = xsd_parser.get_tree()
        expected = "childElement"

        node = tree.find_node_by_name(expected)

        assert node.name == expected

    def test_tree_find_node_by_name_returns_None_when_node_not_found(
        self, xsd_parser,
    ):
        tree = xsd_parser.get_tree()

        node = tree.find_node_by_name("unknown")

        assert node is None

    def test_get_documentation_returns_valid_when_exists(self, xsd_parser):
        tree = xsd_parser.get_tree()

        doc = tree.root.get_doc()

        assert doc.value == "Documentation ``example``."

    def test_get_documentation_returns_valid_other_language(self, xsd_parser):
        tree = xsd_parser.get_tree()

        doc = tree.root.get_doc("es")

        assert doc.value == "``Ejemplo`` de documentación."

    def test_get_documentation_should_return_no_documentation_when_not_exists(
        self, xsd_parser,
    ):
        tree = xsd_parser.get_tree()

        doc = tree.root.get_doc("de")

        assert doc.value == MSG_NO_DOCUMENTATION_AVAILABLE
