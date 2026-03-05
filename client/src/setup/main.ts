import { ExtensionContext, ProgressLocation, window } from "vscode";
import { LocalStorageService } from "../configuration/storage";
import { Constants } from "../constants";
import { execAsync, forceDeleteDirectory as removeDirectory } from "../utils";
import { logger } from "../logger";
import { PackageManagerFactory } from "./packageManager";
import { PythonFinder } from "./pythonFinder";
import { PythonEnvironment } from "./pythonEnvironment";
import { ERROR_MESSAGES, PROGRESS_MESSAGES, SHOW_OUTPUT_BUTTON } from "./constants";

/**
 * Show an error notification with a "Show Output" action button that opens
 * the extension output panel when clicked.
 */
async function showErrorWithOutput(message: string): Promise<void> {
    const selection = await window.showErrorMessage(message, SHOW_OUTPUT_BUTTON);
    if (selection === SHOW_OUTPUT_BUTTON) {
        logger.show();
    }
}

/**
 * Ensures that the Language server is installed in the extension's virtual environment
 * and returns the Python path of the virtual environment or undefined if there was
 * a problem or the user cancelled the installation.
 * @param context The extension context
 */
export async function installLanguageServer(
    context: ExtensionContext
): Promise<string | undefined> {
    const storageManager = new LocalStorageService(context.globalState);
    const packageManager = await PackageManagerFactory.create(execAsync);
    const pythonFinder = new PythonFinder(execAsync);

    // Check if the LS is already installed
    const environment = PythonEnvironment.create(
        context.extensionPath,
        Constants.LS_VENV_NAME,
        packageManager,
        execAsync
    );

    if (environment.exists()) {
        if (await environment.isHealthy()) {
            const venvPython = environment.getPythonPath();
            const isInstalled = await packageManager.isPackageInstalled(
                venvPython,
                Constants.GALAXY_LS_PACKAGE,
                Constants.GALAXY_LS_VERSION
            );
            if (isInstalled) {
                logger.info(`${Constants.GALAXY_LS_PACKAGE} already installed at ${environment.getEnvironmentPath()}`);
                return Promise.resolve(venvPython);
            }
        } else {
            // The venv Python binary cannot execute — the base interpreter it was built
            // against has likely moved or been removed (e.g. uv-managed Python with a
            // temporary build prefix like /install). Delete it so it gets recreated.
            logger.warn(
                `Virtual environment at ${environment.getEnvironmentPath()} is broken ` +
                `(base Python may have moved or been removed). Deleting and recreating...`
            );
            removeDirectory(environment.getEnvironmentPath());
        }
    }

    const storedPython = storageManager.getStoredPython();
    logger.debug(`Stored Python path: ${storedPython}`);

    // Install with progress
    return window.withProgress(
        {
            location: ProgressLocation.Window,
            title: PROGRESS_MESSAGES.INSTALLING,
        },
        async (): Promise<string> => {
            try {
                // Find suitable Python installation
                if (!environment.exists()) {
                    logger.info(PROGRESS_MESSAGES.CHECKING_VERSION);

                    const discoveryResult = await pythonFinder.findPython(storedPython);

                    if (!discoveryResult.success || !discoveryResult.pythonPath) {
                        const message = discoveryResult.error || ERROR_MESSAGES.PYTHON_REQUIRED(Constants.REQUIRED_PYTHON_VERSION);
                        logger.error(`Python discovery failed: ${message}`);
                        await showErrorWithOutput(message);
                        throw new Error(message);
                    }

                    const python = discoveryResult.pythonPath;

                    // Store the validated Python path
                    if (python !== storedPython) {
                        storageManager.setStoredPython(python);
                        logger.debug(`Stored Python path: ${python}`);
                    }

                    // Create virtual environment
                    logger.info(PROGRESS_MESSAGES.CREATING_VENV);
                    await environment.create(python, Constants.LS_VENV_NAME, context.extensionPath);

                    // Upgrade environment dependencies
                    await environment.upgrade();
                }

                const venvPython = environment.getPythonPath();
                logger.info(`Using Python from: ${venvPython}`);

                // Install language server package
                logger.info(PROGRESS_MESSAGES.INSTALLING_PACKAGE(Constants.GALAXY_LS_PACKAGE));
                const installResult = await packageManager.install(
                    venvPython,
                    Constants.GALAXY_LS_PACKAGE,
                    Constants.GALAXY_LS_VERSION
                );

                if (!installResult.success) {
                    logger.error(`Failed to install Galaxy Language Server package: ${installResult.error}`);
                    removeDirectory(environment.getEnvironmentPath());
                    await showErrorWithOutput(ERROR_MESSAGES.INSTALLATION_FAILED);
                    throw new Error(installResult.error || ERROR_MESSAGES.INSTALLATION_FAILED);
                }

                logger.info(`${Constants.GALAXY_LS_PACKAGE} installed successfully`);

                if (storageManager.isServerFirstTimeInstall()) {
                    storageManager.setServerInstalled();
                }

                return venvPython;
            } catch (err: any) {
                logger.error(`Language server installation error: ${err}`);
                await showErrorWithOutput(err.message || String(err));
                throw err;
            }
        }
    );
}

/**
 * Simplified version of `installLanguageServer` without UI interaction.
 * This is meant to be used in testing environments.
 * @param installPath The path to install the local Python environment
 */
export async function silentInstallLanguageServerForTesting(installPath: string): Promise<string | undefined> {
    const serverPath = installPath.replace("client", "server");
    const packageManager = await PackageManagerFactory.create(execAsync);
    const pythonFinder = new PythonFinder(execAsync);

    const environment = PythonEnvironment.create(
        installPath,
        Constants.LS_VENV_NAME,
        packageManager,
        execAsync
    );

    return window.withProgress(
        {
            location: ProgressLocation.Window,
            title: PROGRESS_MESSAGES.INSTALLING_DEV,
        },
        async (): Promise<string> => {
            try {
                // Find suitable Python installation
                if (!environment.exists()) {
                    logger.info("Checking Python version for development mode...");

                    const discoveryResult = await pythonFinder.findPython(null);

                    if (!discoveryResult.success || !discoveryResult.pythonPath) {
                        const message = ERROR_MESSAGES.PYTHON_REQUIRED(Constants.REQUIRED_PYTHON_VERSION);
                        logger.error("Python version check failed - required version not found");
                        throw new Error(message);
                    }

                    const python = discoveryResult.pythonPath;

                    // Create virtual environment
                    logger.info("Creating virtual environment for development...");
                    await environment.create(python, Constants.LS_VENV_NAME, installPath);

                    // Upgrade environment dependencies
                    await environment.upgrade();
                }

                const venvPython = environment.getPythonPath();
                logger.info(`Using Python from virtual environment: ${venvPython}`);

                // Install development server
                logger.info(PROGRESS_MESSAGES.INSTALLING_DEV_PACKAGE(Constants.GALAXY_LS_PACKAGE));
                const installResult = await packageManager.installEditable(venvPython, serverPath);

                if (!installResult.success) {
                    logger.error("Development server installation failed");
                    removeDirectory(environment.getEnvironmentPath());
                    throw new Error(ERROR_MESSAGES.INSTALLATION_FAILED);
                }

                logger.info(`${Constants.GALAXY_LS_PACKAGE} development version installed successfully`);

                return venvPython;
            } catch (err: any) {
                logger.error(`Development server installation error: ${err.message || err}`);
                throw err;
            }
        }
    );
}
