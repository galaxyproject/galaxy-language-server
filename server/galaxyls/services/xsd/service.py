"""Utilities to validate Galaxy xml tool wrappers and extract
information from the XSD schema.
"""

from typing import (
    List,
    Optional,
)

from lxml import etree
from pygls.lsp.types import (
    Diagnostic,
    MarkupContent,
    MarkupKind,
)

from galaxyls.services.context import XmlContext
from galaxyls.services.xml.document import XmlDocument
from galaxyls.services.xsd.constants import (
    MSG_NO_DOCUMENTATION_AVAILABLE,
    TOOL_XSD_FILE,
)
from galaxyls.services.xsd.parser import GalaxyToolXsdParser
from galaxyls.services.xsd.types import XsdBase
from galaxyls.services.xsd.validation import GalaxyToolSchemaValidationService

NO_DOC_MARKUP = MarkupContent(kind=MarkupKind.Markdown, value=MSG_NO_DOCUMENTATION_AVAILABLE)


class GalaxyToolXsdService:
    """Galaxy tool Xml Schema Definition service.

    This service provides functionality to extract information from
    the XSD schema and validate XML files against it.
    """

    def __init__(self) -> None:
        """Initializes the validator by loading the XSD."""
        self.xsd_doc: etree._ElementTree = etree.parse(str(TOOL_XSD_FILE))
        self.xsd_schema = etree.XMLSchema(self.xsd_doc)
        self.xsd_parser = GalaxyToolXsdParser(self.xsd_doc.getroot())
        self.validator = GalaxyToolSchemaValidationService(self.xsd_schema)

    def validate_document(self, xml_document: XmlDocument) -> List[Diagnostic]:
        """Validates the Galaxy tool xml using the XSD schema and returns a list
        of diagnostics if there are any problems.
        """
        return self.validator.validate_document(xml_document)

    def get_documentation_for(self, context: XmlContext) -> MarkupContent:
        """Gets the documentation annotated in the XSD about the
        given element name (node or attribute).
        """
        if context.xsd_element:
            element: Optional[XsdBase]
            if context.is_tag:
                element = context.xsd_element
            elif context.is_attribute_key and context.node and context.node.name:
                element = context.xsd_element.attributes.get(context.node.name)
            if element:
                return element.get_doc()
        return NO_DOC_MARKUP
