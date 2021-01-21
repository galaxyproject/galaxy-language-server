from typing import Dict, Optional

from anytree.search import findall
from pygls.types import Position, Range
from pygls.workspace import Document

from .nodes import XmlContainerNode, XmlElement, XmlSyntaxNode
from .types import DocumentType, NodeType
from .utils import convert_document_offset_to_position, convert_document_offsets_to_range


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
        try:
            found = findall(self.root, filter_=lambda node: node.name == "expand", mincount=1)
            return len(found) > 0
        except BaseException:
            return False

    @property
    def document_type(self) -> DocumentType:
        """The type of this document (if it is supported) or UNKNOWN."""
        if self.root and self.root.name:
            return self.supported_document_types.get(self.root.name, DocumentType.UNKNOWN)
        return DocumentType.UNKNOWN

    @property
    def is_unknown(self) -> bool:
        """Indicates if the document is of unknown type."""
        return self.document_type == DocumentType.UNKNOWN

    @property
    def is_macros_file(self) -> bool:
        """Indicates if the document is a macro definition file."""
        return self.document_type == DocumentType.MACROS

    def get_node_at(self, offset: int) -> Optional[XmlSyntaxNode]:
        """Gets the syntax node a the given offset."""
        return self.root.find_node_at(offset)

    def get_content_range(self, element: XmlContainerNode) -> Optional[Range]:
        """Gets the Range positions for the given XML element's content in the document.

        Args:
            element (XmlContainerNode): The XML element to determine it's content range positions.

        Returns:
            Optional[Range]: The range positions for the content of the given XML element.
        """
        start_offset, end_offset = element.get_content_offsets()
        if start_offset < 0 or end_offset < 0:
            return None
        return convert_document_offsets_to_range(self.document, start_offset, end_offset)

    def get_position_before(self, element: XmlElement) -> Position:
        """Return the position in the document before the given element.

        Args:
            element (XmlElement): The element used to find the position.

        Returns:
            Position: The position just before the element declaration.
        """
        return convert_document_offset_to_position(self.document, element.start)

    def get_position_after(self, element: XmlElement) -> Position:
        """Return the position in the document after the given element.

        Args:
            element (XmlElement): The element used to find the position.

        Returns:
            Position: The position just after the element declaration.
        """
        if element.is_self_closed:
            return convert_document_offset_to_position(self.document, element.end)
        return convert_document_offset_to_position(self.document, element.end_offset)
