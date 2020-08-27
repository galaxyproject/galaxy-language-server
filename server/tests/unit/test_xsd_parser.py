from lxml import etree
from ...services.xsd.parser import XsdParser
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
      <xs:element name="firstElement" type="xs:integer"/>
      <xs:element name="secondElement" type="xs:string"/>
      <xs:element name="thirdElement" type="CustomIntSimpleType">
        <xs:complexType>
          <xs:sequence>
            <xs:element name="childElement" type="xs:integer">
              <xs:annotation>
                <xs:documentation xml:lang="en">
                  <![CDATA[
                    This is a multiline
                    documentation example.
                  ]]>
                </xs:documentation>
              </xs:annotation>
            </xs:element>
          </xs:sequence>
          <xs:attribute name="testDate" type="xs:date"/>
        </xs:complexType>
      </xs:element>
    </xs:sequence>
    <xs:attribute name="id" type="xs:integer" use="required"/>
    <xs:attribute name="value" type="ValueSimpleType"/>
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
</xs:schema>
"""


def _get_test_parser() -> XsdParser:
    root = etree.fromstring(TEST_XSD)
    parser = XsdParser(root)
    return parser


def test_get_tree_returns_valid_element_names():
    parser = _get_test_parser()

    tree = parser.get_tree()

    assert len(tree.ancestors) == 0
    assert len(tree.descendants) == 4
    assert tree.name == "testElement"
    assert tree.children[0].name == "firstElement"
    assert tree.children[1].name == "secondElement"
    assert tree.children[2].name == "thirdElement"
    assert tree.children[2].children[0].name == "childElement"


def test_get_tree_returns_valid_attribute_names():
    parser = _get_test_parser()

    tree = parser.get_tree()

    assert len(tree.attributes) == 2
    assert tree.attributes[0].name == "id"
    assert tree.attributes[1].name == "value"
    assert tree.children[2].attributes[0].name == "testDate"


def test_get_documentation_returns_valid_when_exists():
    parser = _get_test_parser()
    tree = parser.get_tree()

    doc = tree.get_doc()

    assert doc == "Documentation ``example``."


def test_get_documentation_returns_valid_when_language_is_given():
    parser = _get_test_parser()
    tree = parser.get_tree()

    doc = tree.get_doc("es")

    assert doc == "``Ejemplo`` de documentación."


def test_get_documentation_should_return_no_documentation_when_not_exists():
    parser = _get_test_parser()
    tree = parser.get_tree()

    doc = tree.get_doc("de")

    assert doc == MSG_NO_DOCUMENTATION_AVAILABLE
