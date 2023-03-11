from typing import (
    NamedTuple,
    Type,
    TypeVar,
)

from lsprotocol import converters as cv

T = TypeVar("T")


def convert_to(params: NamedTuple, type: Type[T]) -> T:
    """Given a namedtuple, converts it into the given model type."""
    converter = cv.get_converter()
    obj = converter.structure(params, type)
    return obj
