"""This module contains definitions for constants used by the Galaxy Tools Language Server."""


class Commands:
    AUTO_CLOSE_TAGS = "gls.completion.autoCloseTags"
    GENERATE_TESTS = "gls.generate.tests"
    GENERATE_COMMAND = "gls.generate.command"
    SORT_SINGLE_PARAM_ATTRS = "gls.sort.singleParamAttributes"
    SORT_DOCUMENT_PARAMS_ATTRS = "gls.sort.documentParamsAttributes"
    DISCOVER_TESTS_IN_WORKSPACE = "gls.tests.discoverInWorkspace"
    DISCOVER_TESTS_IN_DOCUMENT = "gls.tests.discoverInDocument"
    GENERATE_EXPANDED_DOCUMENT = "gls.generate.expandedDocument"


class DiagnosticCodes:
    INVALID_EXPANDED_TOOL = 101
