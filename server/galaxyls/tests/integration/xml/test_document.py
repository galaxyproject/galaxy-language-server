import pytest

from galaxyls.tests.unit.utils import TestUtils


class TestXmlDocumentClass:
    @pytest.mark.parametrize(
        "source, name, expected_count",
        [
            ("", "a", 0),
            ("<test></test>", "a", 0),
            ("<test><a></test>", "a", 1),
            ("<test><a/></test>", "a", 1),
            ("<test><a/><a/></test>", "a", 2),
            ("<test><a></a></test>", "a", 1),
            ("<test><a></a><a></a></test>", "a", 2),
            ("<test><a></a><other><a></a></other></test>", "a", 2),
            ('<test a="value"><a></a></test>', "a", 1),
            ('<test attr="a"><a></a></test>', "a", 1),
        ],
    )
    def test_find_all_elements_with_name_returns_expected_count(self, source: str, name: str, expected_count: int) -> None:
        xml_document = TestUtils.from_source_to_xml_document(source)

        elements = xml_document.find_all_elements_with_name(name)

        assert len(elements) == expected_count
