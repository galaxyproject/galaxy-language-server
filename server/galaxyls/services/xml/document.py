from typing import Dict, Optional
from anytree.search import find

from pygls.types import Range
from pygls.workspace import Document

from .nodes import XmlElement, XmlSyntaxNode
from .types import DocumentType, NodeType
from .utils import convert_document_offsets_to_range


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
    def uses_macros(self) -> bool:
        """Indicates if this XML document contains any <expand> element.

        Returns:
            bool: True if the tool contains at least one <expand> elements.
        """
        if self.root is None:
            return False
        node = find(self.root, filter_=lambda node: node.name == "expand")
        return node is not None

    @property
    def document_type(self) -> DocumentType:
        """The type of this document (if it is supported) or UNKNOWN."""
        if self.root and self.root.name:
            return self.supported_document_types.get(self.root.name, DocumentType.UNKNOWN)
        return DocumentType.UNKNOWN

    def get_node_at(self, offset: int) -> Optional[XmlSyntaxNode]:
        """Gets the syntax node a the given offset."""
        return self.root.find_node_at(offset)

    def get_element_content_range(self, element: XmlElement) -> Optional[Range]:
        """Gets the Range positions for the given XML element's content in the document.

        Args:
            element (XmlElement): The XML element to determine it's content range positions.

        Returns:
            Optional[Range]: The range positions for the content of the given XML element.
        """
        start_offset, end_offset = element.get_content_offsets()
        if start_offset < 0 or end_offset < 0:
            return None
        return convert_document_offsets_to_range(self.document, start_offset, end_offset)
