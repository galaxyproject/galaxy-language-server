import re
from typing import Optional

from pygls.workspace import Document

from galaxyls.services.xml.types import DocumentType

MAX_PEEK_CONTENT = 1000
TAG_GROUP_NAME = "root_tag"
TAG_REGEX = r"[\n\s]*?.*?[\n\s]*?<(?!\?)(?!\!)(?P<root_tag>[\w]*)"
SUPPORTED_ROOT_TAGS = [e.name.lower() for e in DocumentType if e != DocumentType.UNKNOWN]


class DocumentValidator:
    """Provides some utilities to quickly check documents without completely parse them beforehand."""

    @classmethod
    def has_valid_root(cls, document: Document) -> bool:
        """Checks if the document's root element matches one of the supported types
        or is an empty document."""
        if DocumentValidator.is_empty_document(document):
            return True
        root_tag = DocumentValidator.get_document_root_tag(document)
        if root_tag is not None:
            return root_tag == "" or root_tag in SUPPORTED_ROOT_TAGS
        return False

    @classmethod
    def is_tool_document(cls, document: Document) -> bool:
        """Checks if the document's root element is <tool>."""
        root = DocumentValidator.get_document_root_tag(document)
        if root is not None:
            root_tag = root.upper()
            return root_tag == DocumentType.TOOL.name
        return False

    @classmethod
    def is_empty_document(cls, document: Document) -> bool:
        """Whether the document is empty or just contains spaces or empty lines."""
        return not document.source or document.source.isspace()

    @classmethod
    def get_document_root_tag(cls, document: Document) -> Optional[str]:
        """Checks the first MAX_PEEK_CONTENT characters of the document for a root tag and
        returns the name of the tag if found."""
        content_peek = document.source[:MAX_PEEK_CONTENT]
        match = re.search(TAG_REGEX, content_peek)
        if match:
            group = match.group(TAG_GROUP_NAME)
            return group
        return None
