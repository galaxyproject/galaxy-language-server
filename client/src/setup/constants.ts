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
    
    PYTHON_INVALID: (version: string) => 
        `The selected file is not a valid Python ${version} path!`,
    
    INSTALLATION_FAILED: 
        "There was a problem trying to install the Galaxy language server. Check the logs under Help > Developer Tools > Console or try reloading VS Code.",
    
    INSTALLATION_CANCELLED: 
        "Language server installation cancelled by user",
    
    VERSION_CHECK_FAILED: 
        "Failed to check Python version",
    
    ENVIRONMENT_CREATION_FAILED: 
        "Failed to create virtual environment",
    
    PACKAGE_INSTALLATION_FAILED: (packageName: string) => 
        `Failed to install Python package ${packageName}`,
};

/**
 * User-facing messages.
 */
export const USER_MESSAGES = {
    INSTALL_PROMPT: (pythonVersion: string) =>
        `Galaxy Tools needs to install the Galaxy Language Server Python package to continue. This will be installed in a virtual environment inside the extension and will require Python ${pythonVersion}`,
    
    SELECT_PYTHON_PROMPT: (pythonVersion: string) =>
        `Please select your Python ${pythonVersion} path to continue the installation. This python will be used to create a virtual environment inside the extension directory.`,
    
    INSTALL_COMPLETE: "Galaxy Tools extension is ready!",
    
    INSTALL_MORE_INFO_URL: "https://github.com/galaxyproject/galaxy-language-server/blob/main/client/README.md#installation",
};

/**
 * Progress messages shown during installation.
 */
export const PROGRESS_MESSAGES = {
    INSTALLING: "Installing/updating Galaxy language server...",
    INSTALLING_DEV: "Installing Galaxy language server...",
    CHECKING_VERSION: "Checking Python version compatibility...",
    CREATING_VENV: "Creating virtual environment...",
    UPGRADING_DEPS: "Upgrading virtual environment dependencies...",
    INSTALLING_PACKAGE: (packageName: string) => `Installing ${packageName}...`,
    INSTALLING_DEV_PACKAGE: (packageName: string) => `Installing latest DEV version of ${packageName}...`,
};
