from pytest_mock import MockerFixture

from ...services.xsd.constants import MSG_NO_DOCUMENTATION_AVAILABLE
from ...services.xsd.service import GalaxyToolXsdService


class TestGalaxyToolXsdServiceClass:
    def test_get_documentation_for_unknown_node_attribute_returns_no_documentation(self, mocker: MockerFixture) -> None:
        service = GalaxyToolXsdService()
        fake_context = mocker.Mock()
        fake_context.xsd_element = None

        doc = service.get_documentation_for(fake_context)

        assert doc.value == MSG_NO_DOCUMENTATION_AVAILABLE

    def test_get_documentation_for_annotated_element(self, mocker: MockerFixture) -> None:
        service = GalaxyToolXsdService()
        fake_context = mocker.Mock()
        fake_context.is_tag = True
        fake_context.is_attribute_key = False
        fake_context.stack = ["tool"]

        doc = service.get_documentation_for(fake_context)

        assert doc.value
        assert doc.value != MSG_NO_DOCUMENTATION_AVAILABLE

    def test_get_documentation_for_element_using_annotated_type(self, mocker: MockerFixture) -> None:
        service = GalaxyToolXsdService()
        fake_context = mocker.Mock()
        fake_context.is_tag = True
        fake_context.is_attribute_key = False
        fake_context.stack = ["tool", "macros"]

        doc = service.get_documentation_for(fake_context)

        assert doc.value
        assert doc.value != MSG_NO_DOCUMENTATION_AVAILABLE

    def test_get_documentation_for_annotated_attribute(self, mocker: MockerFixture) -> None:
        service = GalaxyToolXsdService()
        fake_context = mocker.Mock()
        fake_context.is_tag = False
        fake_context.is_attribute_key = True
        fake_context.token.name = "id"
        fake_context.stack = ["tool"]

        doc = service.get_documentation_for(fake_context)

        assert doc.value
        assert doc.value != MSG_NO_DOCUMENTATION_AVAILABLE
