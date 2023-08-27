from lsprotocol.types import (
    Position,
    Range,
)

from galaxyls.services.links import DocumentLinksProvider
from galaxyls.tests.unit.utils import TestUtils


class TestDocumentLinksProviderClass:
    def test_returns_no_links_when_no_test_params(self) -> None:
        xml_document = TestUtils.from_source_to_xml_document(
            """
<tool>
    <tests>
    </tests>
</tool>
"""
        )

        provider = DocumentLinksProvider()

        actual = provider.get_document_links(xml_document)

        assert actual == []

    def test_returns_only_file_links(self) -> None:
        xml_document = TestUtils.from_source_to_xml_document(
            """
<tool>
    <inputs>
        <param name="input1" type="data" format="txt"/>
        <param name="input2" type="data" format="txt"/>
        <param name="num" type="integer" format="txt"/>
        <param name="empty" type="data" format="txt"/>
        <param name="bool_param" type="boolean"/>
    </inputs>
    <tests>
        <test>
            <param name="input1" value="my test file.txt"/>
            <param name="bool_param" value="false"/>
        </test>
        <test>
            <param name="input2" value="data_file_without_extension"/>
            <param name="num" value="3"/>
            <param name="empty" value=""/>
        </test>
    </tests>
</tool>
"""
        )

        provider = DocumentLinksProvider()

        actual = provider.get_document_links(xml_document)

        assert len(actual) == 2

        assert actual[0].target is not None
        assert actual[0].target.endswith("/test-data/my%20test%20file.txt")
        assert actual[0].range == Range(start=Position(line=11, character=40), end=Position(line=11, character=56))

        assert actual[1].target is not None
        assert actual[1].target.endswith("/test-data/data_file_without_extension")
        assert actual[1].range == Range(start=Position(line=15, character=40), end=Position(line=15, character=67))
