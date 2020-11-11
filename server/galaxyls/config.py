from enum import Enum, unique
from typing import Any, Optional


@unique
class CompletionMode(Enum):
    """Supported types of XML documents."""

    AUTO = 1
    INVOKE = 2
    DISABLED = 3


class GalaxyToolsConfiguration:

    SECTION = "galaxyTools"

    def __init__(self, config: Optional[Any] = None) -> None:
        self._config = config
        self._completion_mode = self._to_completion_mode(self._config.completion.mode)
        self._auto_close_tags: bool = self._config.completion.autoCloseTags == "true"

    @property
    def completion_mode(self) -> CompletionMode:
        return self._completion_mode

    @property
    def auto_close_tags(self) -> bool:
        return self._auto_close_tags

    def _to_completion_mode(self, setting: str) -> CompletionMode:
        try:
            return CompletionMode[setting.upper()]
        except BaseException:
            return CompletionMode.AUTO
