from pygls.workspace import Document


def get_fake_document(source: str) -> Document:
    return Document("file://fake_doc.xml", source)
