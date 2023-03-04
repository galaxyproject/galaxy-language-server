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

    def test_init_configuration_from_dict(self):
        config_dict = {
            "server": {"silentInstall": False},
            "completion": {"mode": "disabled", "autoCloseTags": True},
            "planemo": {
                "enabled": True,
                "envPath": "/path/to/planemo",
                "galaxyRoot": "/path/to/galaxy",
                "testing": {"enabled": True, "autoTestDiscoverOnSaveEnabled": True, "extraParams": "--debug"},
            },
        }

        config = GalaxyToolsConfiguration.from_config_dict(config_dict)

        assert config.server.silent_install is False
        assert config.completion.mode == CompletionMode.DISABLED
        assert config.completion.auto_close_tags is True
        assert config.planemo.enabled is True
        assert config.planemo.env_path == "/path/to/planemo"
        assert config.planemo.galaxy_root == "/path/to/galaxy"
        assert config.planemo.testing.enabled is True
        assert config.planemo.testing.auto_test_discover_on_save_enabled is True
        assert config.planemo.testing.extra_params == "--debug"
