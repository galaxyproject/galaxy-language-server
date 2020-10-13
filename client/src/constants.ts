import { extensions } from "vscode";

export const EXTENSION_JSON = extensions.getExtension("davelopez.galaxy-tools")?.packageJSON;
export const EXTENSION_NAME = EXTENSION_JSON.displayName;
export const EXTENSION_PATH = EXTENSION_JSON.extensionLocation.fsPath;

export const IS_WIN = process.platform === "win32";
export const LS_VENV_NAME = "glsenv";
export const GALAXY_LS_PACKAGE = "galaxy-language-server"
export const GALAXY_LS = "galaxyls"

export const PYTHON_UNIX = "python3"
export const PYTHON_WIN = "python.exe"