from typing import (
    NamedTuple,
    Type,
    TypeVar,
)

T = TypeVar("T")


def is_namedtuple_instance(x) -> bool:
    _type = type(x)
    bases = _type.__bases__
    if len(bases) != 1 or bases[0] != tuple:
        return False
    fields = getattr(_type, "_fields", None)
    if not isinstance(fields, tuple):
        return False
    return all(type(i) == str for i in fields)


def unpack(obj):
    """Unpacks a named tuple into a dictionary.
    https://stackoverflow.com/a/39235373"""
    if isinstance(obj, dict):
        return {key: unpack(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [unpack(value) for value in obj]
    elif is_namedtuple_instance(obj):
        return {key: unpack(value) for key, value in obj._asdict().items()}
    elif isinstance(obj, tuple):
        return tuple(unpack(value) for value in obj)
    else:
        return obj


def deserialize_command_param(params: NamedTuple, type: Type[T]) -> T:
    """Given a namedtuple, converts it into the given type of pydantic model."""
    params_dict = unpack(params)
    obj = type(**params_dict)  # type: ignore [call-arg]
    return obj
