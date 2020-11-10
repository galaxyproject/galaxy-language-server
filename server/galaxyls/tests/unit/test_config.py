from typing import Any, NamedTuple

from pytest_mock.plugin import MockerFixture

from ...config import CompletionMode, GalaxyToolsConfiguration


class TestGalaxyToolsConfigurationClass:
    def test_init_sets_properties(self, mocker: MockerFixture) -> None:
        mock_config = mocker.Mock()
        mock_config.completion.mode = "invoke"
        mock_config.completion.autoCloseTags = "false"

        config = GalaxyToolsConfiguration(mock_config)

        assert config.completion_mode
        assert not config.auto_close_tags

    def test_unknown_completion_mode_returns_default(self, mocker: MockerFixture) -> None:
        mock_config = mocker.Mock()
        mock_config.completion.mode = "unknown"

        config = GalaxyToolsConfiguration(mock_config)

        assert config.completion_mode == CompletionMode.AUTO
