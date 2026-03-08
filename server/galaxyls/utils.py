from typing import (
    NamedTuple,
    TypeVar,
)

from lsprotocol import converters as cv

T = TypeVar("T")


def convert_to(params: NamedTuple, type: type[T]) -> T:
    """Given a namedtuple, converts it into the given model type."""
    converter = cv.get_converter()
    obj = converter.structure(params, type)
    return obj
