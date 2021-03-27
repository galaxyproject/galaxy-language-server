from galaxyls.config import CompletionMode, GalaxyToolsConfiguration


class TestGalaxyToolsConfigurationClass:
    def test_init_sets_properties(self) -> None:
        mock_config = {
            "completion": {
                "mode": "invoke",
                "autoCloseTags": "false",
            },
        }

        config = GalaxyToolsConfiguration(**mock_config)

        assert config.completion.mode == CompletionMode.INVOKE
        assert not config.completion.auto_close_tags
