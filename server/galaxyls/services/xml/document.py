from typing import Dict, List, Optional

from anytree.search import findall
from pygls.lsp.types import Position, Range
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

    @property
    def is_tool_file(self) -> bool:
        """Indicates if the document is a tool definition file."""
        return self.document_type == DocumentType.TOOL

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

    def get_element_name_range(self, element: XmlElement) -> Optional[Range]:
        """Gets the Range positions for the given XML element's name in the document.

        Args:
            element (XmlElement): The XML element to determine it's name range positions.

        Returns:
            Optional[Range]: The range positions for the name of the given XML element.
        """
        start_offset = element.name_start_offset
        end_offset = element.name_end_offset
        if start_offset < 0 or end_offset < 0:
            return None
        return convert_document_offsets_to_range(self.document, start_offset, end_offset)

    def get_full_range(self, node: XmlSyntaxNode) -> Optional[Range]:
        """Gets the Range positions for the given XML node in the document.

        Args:
            node (XmlSyntaxNode): The XML node to determine it's range positions.

        Returns:
            Optional[Range]: The range positions for the entire node.
        """
        if node.start < 0 or node.end < 0:
            return None
        return convert_document_offsets_to_range(self.document, node.start, node.end)

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

    def find_all_elements_with_name(self, name: str) -> List[XmlElement]:
        """Returns a list with all the elements contained in the document matching the given name."""
        if self.root:
            found = findall(self.root, filter_=lambda node: isinstance(node, XmlElement) and node.name == name)
            return list(found)
        return []

    def get_text_between_offsets(self, start: int, end: int) -> str:
        """Gets the text content between the start and end offsets."""
        return self.document.source[start:end]
