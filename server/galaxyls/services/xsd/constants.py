"""This module contains constants related to XSD processing.
"""

import galaxy.tool_util
from pathlib import Path

TOOL_XSD_FILE = Path(galaxy.tool_util.__file__).parent / "xsd" / "galaxy.xsd"

# Maximum depth when the schema contains recursive definitions
MAX_RECURSION_DEPTH = 25

# Schema namespace
XS_NAMESPACE = "{http://www.w3.org/2001/XMLSchema}"

# XSD elements
XS_ATTRIBUTE = f"{XS_NAMESPACE}attribute"
XS_COMPLEX_TYPE = f"{XS_NAMESPACE}complexType"
XS_ELEMENT = f"{XS_NAMESPACE}element"
XS_SCHEMA = f"{XS_NAMESPACE}schema"
XS_SEQUENCE = f"{XS_NAMESPACE}sequence"
XS_ALL = f"{XS_NAMESPACE}all"
XS_CHOICE = f"{XS_NAMESPACE}choice"
XS_SIMPLE_TYPE = f"{XS_NAMESPACE}simpleType"
XS_GROUP = f"{XS_NAMESPACE}group"
XS_ATTRIBUTE_GROUP = f"{XS_NAMESPACE}attributeGroup"
XS_SIMPLE_CONTENT = f"{XS_NAMESPACE}simpleContent"
XS_COMPLEX_CONTENT = f"{XS_NAMESPACE}complexContent"
XS_EXTENSION = f"{XS_NAMESPACE}extension"

# Messages
MSG_NO_DOCUMENTATION_AVAILABLE = "No documentation available"
