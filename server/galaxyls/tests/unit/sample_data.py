from pygls.workspace import Document

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
      <xs:element name="firstElement" type="CustomIntSimpleType" minOccurs="0" maxOccurs="unbounded">
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
            <xs:element name="childElement" type="TestSimpleContent" minOccurs="1" maxOccurs="1"/>
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

TEST_TOOL_01 = """<tool id="test" name="Test Tool 01" version="0.1.0">
    <command detect_errors="exit_code"><![CDATA[
        TODO: Fill in command template.
    ]]></command>
    <inputs>
    </inputs>
    <outputs>
    </outputs>
    <help><![CDATA[
        TODO: Fill in help.
    ]]></help>
</tool>
"""
TEST_TOOL_01_DOCUMENT = Document("file://test01.xml", TEST_TOOL_01)

TEST_TOOL_WITH_MACRO_01 = """
<tool id="test_with_macro" name="Test with macro 01" version="@WRAPPER_VERSION@">
    <macros>
        <import>macros.xml</import>
    </macros>
    <expand macro="inputs" />
</tool>"""
TEST_TOOL_WITH_MACRO_01_DOCUMENT = Document("file://test_with_macro_01.xml", TEST_TOOL_WITH_MACRO_01)

TEST_MACRO_01 = """
<macros>
    <token name="@WRAPPER_VERSION@">0.1.0</token>
    <macro name="inputs">
        <inputs/>
    </macro>
</macros>
"""
TEST_MACRO_01_DOCUMENT = Document("file://macros.xml", TEST_MACRO_01)


TEST_INVALID_TOOL_01_DOCUMENT = Document("file://test_invalid_01.xml", "<tool></tool>")

TEST_SYNTAX_ERROR_TOOL_01_DOCUMENT = Document("file://test_syntax_error_01.xml", "tool")

TEST_TOOL_WITH_PROLOG = """<?xml version="1.0" encoding="UTF-8"?>
<tool id="test" name="Test Tool" version="0.1.0">
    <inputs/>
    <outputs/>
</tool>
"""
TEST_TOOL_WITH_PROLOG_DOCUMENT = Document("file://test_prolog.xml", TEST_TOOL_WITH_PROLOG)

TEST_TOOL_WITH_INPUTS = """
<tool id="test" name="Test Tool" version="0.1.0">
    <inputs>
      <param name="param-01" type="text"/>
      <param name="param-02" type="boolean"/>
      <conditional name="c1">
          <param name="action" type="select">
              <option value="a1" selected="True">A 1</option>
              <option value="a2">A 2</option>
          </param>
          <when value="a1">
              <param name="p_c1_a1_1" type="text" />
              <param name="p_c1_a1_2" type="boolean" />
              <param name="p_c1_a1_hidden" type="hidden" value="False" />
          </when>
          <when value="a2">
              <param name="p_c1_a2" type="text" />
              <conditional name="c2">
                <param name="action" type="select">
                    <option value="b1" selected="True">B 1</option>
                    <option value="b2">B 2</option>
                </param>
                <when value="b1">
                    <param name="p_c2_b1_1" type="text" />
                </when>
                <when value="b2">
                    <param name="p_c2_b2" type="text" />
                </when>
            </conditional>
          </when>
      </conditional>
    </inputs>
    <outputs/>
</tool>
"""
TEST_TOOL_WITH_INPUTS_DOCUMENT = Document("file://test_prolog.xml", TEST_TOOL_WITH_INPUTS)
