from enum import Enum
from typing import Optional

import attrs


class CompletionMode(str, Enum):
    AUTO = "auto"
    INVOKE = "invoke"
    DISABLED = "disabled"


@attrs.define
class CompletionConfig:
    """Auto-completion feature configuration."""

    mode: CompletionMode = attrs.field(default=CompletionMode.AUTO)
    auto_close_tags: bool = attrs.field(default=True, alias="autoCloseTags")


@attrs.define
class ServerConfig:
    """Language Server specific configuration."""

    silent_install: bool = attrs.field(default=False, alias="silentInstall")


@attrs.define
class PlanemoTestingConfig:
    """Planemo testing configuration."""

    enabled: bool = attrs.field(default=True)
    auto_test_discover_on_save_enabled: bool = attrs.field(default=True, alias="autoTestDiscoverOnSaveEnabled")
    extra_params: str = attrs.field(default="", alias="extraParams")


@attrs.define
class PlanemoConfig:
    """Planemo integration configuration."""

    enabled: bool = attrs.field(default=False)
    env_path: str = attrs.field(default="planemo", alias="envPath")
    galaxy_root: Optional[str] = attrs.field(default=None, alias="galaxyRoot")
    get_cwd: Optional[str] = attrs.field(default=None, alias="getCwd")
    testing: PlanemoTestingConfig = attrs.field(default=PlanemoTestingConfig())


@attrs.define
class GalaxyToolsConfiguration:
    """Galaxy Language Server general configuration."""

    server: ServerConfig = attrs.field(default=ServerConfig())
    completion: CompletionConfig = attrs.field(default=CompletionConfig())
    planemo: PlanemoConfig = attrs.field(default=PlanemoConfig())

    @classmethod
    def from_config_dict(cls, config: dict):
        result = GalaxyToolsConfiguration(
            server=ServerConfig(**config["server"]),
            completion=CompletionConfig(**config["completion"]),
            planemo=PlanemoConfig(**config["planemo"]),
        )
        result.planemo.testing = PlanemoTestingConfig(**config["planemo"]["testing"])
        return result
