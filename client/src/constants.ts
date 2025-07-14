export namespace Constants {
    export const IS_WIN = process.platform === "win32";
    export const LS_VENV_NAME = "glsenv";
    export const GALAXY_LS_PACKAGE = "galaxy-language-server";
    export const GALAXY_LS = "galaxyls";
    export const GALAXY_LS_VERSION = "0.14.0";
    export const LANGUAGE_ID = "galaxytool";
    export const TOOL_DOCUMENT_EXTENSION = "xml";

    export const PYTHON_UNIX = "python3";
    export const PYTHON_WIN = "python.exe";
    export const REQUIRED_PYTHON_VERSION = "3.9+";

    export const EXPAND_DOCUMENT_SCHEMA = "gls-expand";
    export const EXPAND_DOCUMENT_URI_SUFFIX = "%20%28Expanded%29";

    export const PLANEMO_TEST_OUTPUT_CHANNEL = "Planemo Tests";
}

export namespace DiagnosticCodes {
    export const INVALID_EXPANDED_TOOL = 101;
}
