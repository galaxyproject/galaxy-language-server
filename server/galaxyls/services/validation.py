import re

from typing import Optional
from pygls.workspace import Document

from galaxyls.services.xml.types import DocumentType

MAX_PEEK_CONTENT = 100
TAG_GROUP_NAME = "tag"
TAG_REGEX = rf"[\n\s]*?.*?[\n\s]*?<(?!\?)(?P<{TAG_GROUP_NAME}>[\w]*)"


class DocumentValidator:
    """Provides some utilities to quickly check documents without completely parse them beforehand."""

    def has_valid_root(self, document: Document) -> bool:
        """Checks if the document's root element matches one of the supported types."""
        root = self._get_document_root_tag(document)
        if root is not None:
            root_tag = root.upper()
            supported = [e.name for e in DocumentType if e != DocumentType.UNKNOWN]
            return root_tag in supported
        return False

    def _get_document_root_tag(self, document: Document) -> Optional[str]:
        """Checks the first MAX_PEEK_CONTENT characters of the document for a root tag and
        returns the name of the tag if found."""
        content_peek = document.source[:MAX_PEEK_CONTENT]
        match = re.match(TAG_REGEX, content_peek)
        if match:
            group = match.group(TAG_GROUP_NAME)
            return group
        return None
