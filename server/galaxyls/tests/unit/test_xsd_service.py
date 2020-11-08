from ...services.xsd.types import XsdNode, XsdTree
from pytest_mock import MockerFixture
from ...services.context import XmlContext
from ...services.xml.nodes import XmlAttributeKey, XmlElement
from ...services.xsd.constants import MSG_NO_DOCUMENTATION_AVAILABLE
from ...services.xsd.service import GalaxyToolXsdService


class TestGalaxyToolXsdServiceClass:
    def test_get_documentation_for_unknown_node_attribute_returns_no_documentation(self, mocker: MockerFixture) -> None:
        fake_xsd_root = XsdNode("tool", mocker.Mock())
        fake_xsd_tree = XsdTree(fake_xsd_root)
        fake_element = XmlElement()
        fake_element.name = "tool"
        fake_node = XmlAttributeKey("uknownAttr", 0, 10, fake_element)
        fake_context = XmlContext(fake_xsd_tree.root, fake_node)
        service = GalaxyToolXsdService("Test")

        doc = service.get_documentation_for(fake_context)

        assert doc.value == MSG_NO_DOCUMENTATION_AVAILABLE
