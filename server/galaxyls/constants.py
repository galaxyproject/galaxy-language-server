"""This module contains definitions for constants used by the Galaxy Tools Language Server."""

SERVER_NAME = "Galaxy Tools LS"


class Commands:
    AUTO_CLOSE_TAGS = "galaxytools.completion.autoCloseTags"
    GENERATE_TESTS = "galaxytools.generate.tests"
    GENERATE_COMMAND = "galaxytools.generate.command"
    SORT_SINGLE_PARAM_ATTRS = "galaxytools.sort.singleParamAttributes"
    SORT_DOCUMENT_PARAMS_ATTRS = "galaxytools.sort.documentParamsAttributes"
    DISCOVER_TESTS = "galaxytools.tests.discover"
    GENERATE_EXPANDED_DOCUMENT = "galaxytools.generate.expandedDocument"


class DiagnosticCodes:
    INVALID_EXPANDED_TOOL = 101
