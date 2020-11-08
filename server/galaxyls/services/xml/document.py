from typing import Dict, Optional

from pygls.workspace import Document

from .nodes import XmlSyntaxNode, XmlElement
from .types import DocumentType, NodeType


class XmlDocument(XmlSyntaxNode):
    """Represents a parsed XML document.

    This is the root of the XML syntax tree.
    """

    def __init__(self, document: Document):
        super().__init__()
        self.document: Document = document
        self.supported_document_types: Dict[str, DocumentType] = {
            "tool": DocumentType.TOOL,
            "macros": DocumentType.MACROS,
        }

    @property
    def node_type(self) -> NodeType:
        """The type of this node."""
        return NodeType.DOCUMENT

    @property
    def is_empty(self) -> bool:
        """True if the document has no root node."""
        return not self.root

    @property
    def root(self) -> Optional[XmlElement]:
        """The root element of the document.

        Normally this would be tool, macros or any other supported
        kind of element."""
        if len(self.children) == 0:
            return None
        try:
            return next(child for child in self.children if type(child) == XmlElement)
        except StopIteration:
            return None

    @property
    def document_type(self) -> DocumentType:
        """The type of this document (if it is supported) or UNKNOWN."""
        if self.root and self.root.name:
            return self.supported_document_types.get(self.root.name, DocumentType.UNKNOWN)
        return DocumentType.UNKNOWN

    def get_node_at(self, offset: int) -> Optional[XmlSyntaxNode]:
        """Gets the syntax node a the given offset."""
        return self.root.find_node_at(offset)
