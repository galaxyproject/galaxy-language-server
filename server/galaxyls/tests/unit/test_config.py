from galaxyls.config import (
    CompletionConfig,
    CompletionMode,
    GalaxyToolsConfiguration,
    ServerConfig,
)


class TestGalaxyToolsConfigurationClass:
    def test_init_sets_properties(self) -> None:
        fake_server_config = ServerConfig()
        fake_server_config.silent_install = True
        fake_completion_config = CompletionConfig()
        fake_completion_config.mode = CompletionMode.INVOKE
        fake_completion_config.auto_close_tags = False

        config = GalaxyToolsConfiguration(server=fake_server_config, completion=fake_completion_config)

        assert config.server.silent_install is True
        assert config.completion.mode == CompletionMode.INVOKE
        assert config.completion.auto_close_tags is False
