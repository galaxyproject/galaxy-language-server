/**
 * Constants specific to the Python environment setup system.
 */

/**
 * Regular expression pattern to extract version from pip show output.
 */
export const VERSION_PATTERN = /Version: (?<version>\d+\.\d+\.\d+)/m;

/**
 * Label for the "Show Output" action button in error notifications.
 */
export const SHOW_OUTPUT_BUTTON = "Show Output";

/**
 * Error messages used throughout the setup system.
 */
export const ERROR_MESSAGES = {
    PYTHON_REQUIRED: (version: string) =>
        `Python ${version} is required in order to use the language server features.`,

    INSTALLATION_FAILED:
        "There was a problem trying to install the Galaxy language server. Open the 'Galaxy Tools Language Server' Output panel for details or try reloading VS Code.",

    VENV_NO_PIP_WITH_PIP_MANAGER:
        "Failed to create the virtual environment: your Python installation appears to be managed by uv and is incompatible with 'python -m venv'. " +
        "Please install uv (https://docs.astral.sh/uv/) to resolve this issue, or configure a different Python interpreter.",

    VERSION_CHECK_FAILED:
        "Failed to check Python version",

    ENVIRONMENT_CREATION_FAILED:
        "Failed to create virtual environment",

    PACKAGE_INSTALLATION_FAILED: (packageName: string) =>
        `Failed to install Python package ${packageName}`,
};


/**
 * Progress messages shown during installation.
 */
export const PROGRESS_MESSAGES = {
    INSTALLING: "Installing/updating Galaxy language server...",
    INSTALLING_DEV: "Installing GLS development version...",
    CHECKING_VERSION: "Checking Python version compatibility...",
    CREATING_VENV: "Creating virtual environment...",
    INSTALLING_PACKAGE: (packageName: string) => `Installing ${packageName}...`,
    INSTALLING_DEV_PACKAGE: (packageName: string) => `Installing latest DEV version of ${packageName}...`,
};
