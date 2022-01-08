import pytest

from galaxyls.services.context import XmlContextService
from galaxyls.services.xsd.service import GalaxyToolXsdService
from galaxyls.services.xsd.types import XsdTree
from galaxyls.tests.unit.utils import TestUtils


@pytest.fixture()
def galaxy_xsd_tree() -> XsdTree:
    xsd_service = GalaxyToolXsdService("Integration Tests")
    tree = xsd_service.xsd_parser.get_tree()
    return tree


class TestIntegrationXmlContextServiceClass:
    @pytest.mark.parametrize(
        "source_with_mark, expected_element_name",
        [
            (
                "<macros><xml ^",
                "xml",
            ),
            (
                "<macros><xml><repeat ^",
                "repeat",
            ),
            (
                "<macros><xml><param ^",
                "param",
            ),
            (
                "<macros><xml><citation ^",
                "citation",
            ),
            (
                "<macros><xml><expand ^",
                "expand",
            ),
        ],
    )
    def test_context_xsd_node_inside_macros_is_expected(
        self,
        galaxy_xsd_tree: XsdTree,
        source_with_mark: str,
        expected_element_name: str,
    ):
        position, source_without_mark = TestUtils.extract_mark_from_source("^", source_with_mark)
        document = TestUtils.from_source_to_xml_document(source_without_mark)
        service = XmlContextService(galaxy_xsd_tree)

        context = service.get_xml_context(document, position)

        assert context.xsd_element
        assert context.xsd_element.name == expected_element_name

    def test_unknown_element_context_xsd_node_inside_macros_is_none(
        self,
        galaxy_xsd_tree: XsdTree,
    ):
        source_with_mark = "<macros><xml><unknowntag ^"

        position, source_without_mark = TestUtils.extract_mark_from_source("^", source_with_mark)
        document = TestUtils.from_source_to_xml_document(source_without_mark)
        service = XmlContextService(galaxy_xsd_tree)

        context = service.get_xml_context(document, position)

        assert context.xsd_element is None
