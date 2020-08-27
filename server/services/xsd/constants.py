"""This module contains constants related to XSD processing.
"""

import os

TOOL_XSD_FILE = os.path.join(os.path.dirname(__file__), "galaxy.xsd")

# Schema namespace
XS_NAMESPACE = "{http://www.w3.org/2001/XMLSchema}"

# XSD elements
XS_ALL = f"{XS_NAMESPACE}all"
XS_ATTRIBUTE = f"{XS_NAMESPACE}attribute"
XS_COMPLEX_TYPE = f"{XS_NAMESPACE}complexType"
XS_ELEMENT = f"{XS_NAMESPACE}element"
XS_SCHEMA = f"{XS_NAMESPACE}schema"
XS_SEQUENCE = f"{XS_NAMESPACE}sequence"
XS_SIMPLE_TYPE = f"{XS_NAMESPACE}simpleType"

# Messages
MSG_NO_DOCUMENTATION_AVAILABLE = "No documentation available"
