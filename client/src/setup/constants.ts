/**
 * Constants specific to the Python environment setup system.
 */

/**
 * Regular expression pattern to extract version from pip show output.
 */
export const VERSION_PATTERN = /Version: (?<version>\d+\.\d+\.\d+)/m;

/**
 * Error messages used throughout the setup system.
 */
export const ERROR_MESSAGES = {
    PYTHON_REQUIRED: (version: string) =>
        `Python ${version} is required in order to use the language server features.`,

    INSTALLATION_FAILED:
        "There was a problem trying to install the Galaxy language server. Check the logs under Help > Developer Tools > Console or try reloading VS Code.",

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
