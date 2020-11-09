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

    @property
    def completion_mode(self) -> CompletionMode:
        return self._completion_mode

    def _to_completion_mode(self, setting: str) -> CompletionMode:
        try:
            return CompletionMode[setting.upper()]
        except BaseException as e:
            return CompletionMode.AUTO
