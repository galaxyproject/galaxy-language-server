from ...services.context import ContextTokenType, XmlContext
from ...services.xsd.service import GalaxyToolXsdService
from ...services.xsd.constants import MSG_NO_DOCUMENTATION_AVAILABLE


class TestXsdServiceClass:
    def test_get_documentation_for_unknown_node_attribute_returns_no_documentation(self) -> None:
        fake_context = XmlContext()
        fake_context.is_empty = False
        fake_context.token_type = ContextTokenType.ATTRIBUTE_KEY
        fake_context.token_name = "uknownAttr"
        fake_context.node_stack = ["uknown"]
        service = GalaxyToolXsdService("Test")

        doc = service.get_documentation_for(fake_context)

        assert doc.value == MSG_NO_DOCUMENTATION_AVAILABLE
