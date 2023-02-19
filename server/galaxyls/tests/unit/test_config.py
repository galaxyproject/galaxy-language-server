from galaxyls.config import (
    CompletionConfig,
    CompletionMode,
    GalaxyToolsConfiguration,
)


class TestGalaxyToolsConfigurationClass:
    def test_init_sets_properties(self) -> None:
        fake_completion_config = CompletionConfig(mode=CompletionMode.INVOKE, auto_close_tags=False)

        config = GalaxyToolsConfiguration(fake_completion_config)

        assert config.completion.mode == CompletionMode.INVOKE
        assert not config.completion.auto_close_tags
