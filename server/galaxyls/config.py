from typing import Any, Optional


from enum import Enum, unique


@unique
class CompletionMode(Enum):
    """Supported types of XML documents."""

    AUTO = "auto"
    INVOKE = "invoke"
    DISABLED = "disabled"


class GalaxyToolsConfiguration:

    SECTION = "galaxyTools"

    def __init__(self, config: Optional[Any] = None) -> None:
        self._config = config

    @property
    def completion_mode(self) -> CompletionMode:
        try:
            return self._config.completion.mode
        except BaseException:
            return CompletionMode.AUTO
