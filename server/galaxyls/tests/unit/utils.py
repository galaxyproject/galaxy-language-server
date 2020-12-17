from pathlib import Path
from typing import Tuple

from pygls.types import Position
from pygls.workspace import Document

from ...services.xml.constants import NEW_LINE
from ...services.xml.document import XmlDocument
from ...services.xml.parser import XmlDocumentParser


class TestUtils:
    @staticmethod
    def to_document(source: str, uri: str = "file://fake_doc.xml", version: int = 0) -> Document:
        """Converts the given string into a Document.

        Args:
            - source (str): The input string to be converted to Document.
            - uri (str, optional): The uri of the document. Defaults to "file://fake_doc.xml".
            - version (int, optional): The version of the document. Defaults to 0.

        Returns:
            Document: The resulting Document.
        """
        return Document(uri, source, version)

    @staticmethod
    def to_xml_document(source: str, uri: str = "file://fake_doc.xml", version: int = 0) -> XmlDocument:
        """Converts the given string into a parsed XML document.

        Args:
            - source (str): The input string to be converted to XmlDocument.
            - uri (str, optional): The uri of the document. Defaults to "file://fake_doc.xml".
            - version (int, optional): The version of the document. Defaults to 0.

        Returns:
            XmlDocument: The resulting XML document.
        """
        document = Document(uri, source, version)
        xml_document = XmlDocumentParser().parse(document)
        return xml_document

    @staticmethod
    def extract_mark_from_source(mark: str, source_with_mark: str) -> Tuple[Position, str]:
        """Gets a tuple with the position of the mark inside the text and the source text without the mark.

        This is to visually place a mark where the context should be determined in some tests.

        Args:
            mark (str): The character used as mark
            source_with_mark (str): The source text containing the mark character at some position.

        Returns:
            Tuple[Position, str]: The position of the mark and the source text without the mark.
        """
        mark_offset = source_with_mark.find(mark)
        start_line = source_with_mark.count(NEW_LINE, 0, mark_offset)
        line_start_offset = max(source_with_mark.rfind(NEW_LINE, 0, mark_offset), 0)
        start_character = mark_offset - line_start_offset
        mark_position = Position(start_line, start_character)
        source = source_with_mark.replace(mark, "")
        return (mark_position, source)

    @staticmethod
    def get_test_document_from_file(filename: str) -> Document:
        """Gets a Document object from the tests/files directory with the given
        filename.

        Args:
            filename (str): The filename, including the extension.

        Returns:
            Document: The Document object of the test file.
        """
        path = Path(__file__).parent.parent / "files" / filename
        uri = path.as_uri()
        return Document(uri)

    @staticmethod
    def get_test_file_contents(filename: str) -> str:
        """Gets a the text contents of the given filename within the tests/files directory.

        Args:
            filename (str): The filename, including the extension.

        Returns:
            str: The text contents of the test file.
        """
        path = Path(__file__).parent.parent / "files" / filename
        return path.read_text()
