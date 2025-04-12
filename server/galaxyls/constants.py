"""This module contains definitions for constants used by the Galaxy Tools Language Server."""

from lsprotocol.types import (
    Position,
    Range,
)


class Commands:
    AUTO_CLOSE_TAGS = "gls.completion.autoCloseTags"
    GENERATE_TESTS = "gls.generate.tests"
    UPDATE_TESTS_PROFILE = "gls.update.tests"
    GENERATE_COMMAND = "gls.generate.command"
    SORT_SINGLE_PARAM_ATTRS = "gls.sort.singleParamAttributes"
    SORT_DOCUMENT_PARAMS_ATTRS = "gls.sort.documentParamsAttributes"
    DISCOVER_TESTS_IN_WORKSPACE = "gls.tests.discoverInWorkspace"
    DISCOVER_TESTS_IN_DOCUMENT = "gls.tests.discoverInDocument"
    GENERATE_EXPANDED_DOCUMENT = "gls.generate.expandedDocument"
    INSERT_PARAM_REFERENCE = "gls.insert.paramReference"
    INSERT_PARAM_FILTER_REFERENCE = "gls.insert.paramFilterReference"


class DiagnosticCodes:
    INVALID_EXPANDED_TOOL = 101


# Default Document Range and the start of the document
DEFAULT_DOCUMENT_RANGE = Range(
    start=Position(line=0, character=0),
    end=Position(line=0, character=0),
)
