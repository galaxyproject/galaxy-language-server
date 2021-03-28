from enum import Enum

from pydantic import BaseModel


def to_camel(string: str) -> str:
    pascal = "".join(word.capitalize() for word in string.split("_"))
    camel = pascal[0].lower() + pascal[1:]
    return camel


class CompletionMode(str, Enum):
    AUTO = "auto"
    INVOKE = "invoke"
    DISABLED = "disabled"


class ConfigModel(BaseModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True


class CompletionConfig(ConfigModel):
    """Auto-completion feature configuration."""

    mode: CompletionMode = CompletionMode.AUTO
    auto_close_tags: bool = True


class GalaxyToolsConfiguration(ConfigModel):
    """Galaxy Language Server general configuration."""

    completion: CompletionConfig = CompletionConfig()
