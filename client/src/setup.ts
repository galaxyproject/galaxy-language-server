import { join } from "path";
import { existsSync } from "fs";
import { commands, ExtensionContext, ProgressLocation, Uri, window, workspace } from "vscode";
import { Constants } from "./constants";
import { execAsync } from "./utils";
import { LocalStorageService } from "./configuration/storage";

/**
 * Ensures that the Language server is installed in the extension's virtual environment
 * and returns the Python path of the virtual environment or undefined if there was
 * a problem or the user cancelled the installation.
 * @param context The extension context
 */
export async function installLanguageServer(context: ExtensionContext): Promise<string | undefined> {
    const storageManager = new LocalStorageService(context.globalState);

    // Check if the LS is already installed
    let venvPath = getVirtualEnvironmentPath(context.extensionPath, Constants.LS_VENV_NAME);
    if (existsSync(venvPath)) {
        const venvPython = getPythonFromVirtualEnvPath(venvPath);
        const isInstalled = await isPythonPackageInstalled(
            venvPython,
            Constants.GALAXY_LS_PACKAGE,
            Constants.GALAXY_LS_VERSION
        );
        if (isInstalled) {
            console.log(`[gls] ${Constants.GALAXY_LS_PACKAGE} already installed.`);
            return Promise.resolve(venvPython);
        }
    }

    const storedPython = storageManager.getStoredPython();
    console.log(`[gls] getStoredPython: ${storedPython}`);

    if (storedPython === null) {
        const result = await window.showInformationMessage(
            `Galaxy Tools needs to install the Galaxy Language Server Python package to continue. This will be installed in a virtual environment inside the extension and will require Python ${Constants.REQUIRED_PYTHON_VERSION}`,
            ...["Install", "More Info"]
        );

        if (result === undefined) {
            console.log(`[gls] Language server installation cancelled by the user.`);
            return undefined;
        } else if (result === "More Info") {
            commands.executeCommand(
                "vscode.open",
                Uri.parse(
                    "https://github.com/galaxyproject/galaxy-language-server/blob/main/client/README.md#installation"
                )
            );
        }
    }

    // Install with progress
    return window.withProgress(
        {
            location: ProgressLocation.Window,
            title: "Installing/updating Galaxy language server...",
        },
        (progress): Promise<string> => {
            return new Promise<string>(async (resolve, reject) => {
                try {
                    if (!existsSync(venvPath)) {
                        console.log(`[gls] Checking Python version...`);
                        let python = await getPython();

                        if (python === undefined && storedPython !== null) {
                            if (await checkPythonVersion(storedPython)) {
                                console.log(
                                    `[gls] Default python not supported but stored python found. Trying to use stored python: ${storedPython}`
                                );
                                python = storedPython;
                            } else {
                                // The stored python is no longer valid, clear and let the user select a new one
                                storageManager.clearStoredPython();
                            }
                        }

                        if (python === undefined) {
                            await window.showInformationMessage(
                                `Please select your Python ${Constants.REQUIRED_PYTHON_VERSION} path to continue the installation. This python will be used to create a virtual environment inside the extension directory.`,
                                ...["Select"]
                            );
                            python = await selectPythonUsingFileDialog();

                            // User canceled the input
                            if (python === undefined) {
                                const message = `Python ${Constants.REQUIRED_PYTHON_VERSION} is required in order to use the language server features.`;
                                window.showErrorMessage(message);
                                throw new Error(message);
                            } else {
                                storageManager.setStoredPython(python);
                                console.log(`[gls] setStoredPython: ${python}`);
                            }
                        }

                        console.log(`[gls] Creating virtual environment...`);
                        venvPath = await createVirtualEnvironment(
                            python,
                            Constants.LS_VENV_NAME,
                            context.extensionPath
                        );
                    }

                    const venvPython = getPythonFromVirtualEnvPath(venvPath);
                    console.log(`[gls] Using Python from: ${venvPython}`);

                    console.log(`[gls] Installing ${Constants.GALAXY_LS_PACKAGE}...`);
                    const isInstalled = await installPythonPackage(
                        venvPython,
                        Constants.GALAXY_LS_PACKAGE,
                        Constants.GALAXY_LS_VERSION
                    );

                    if (!isInstalled) {
                        const errorMessage = "There was a problem trying to install the Galaxy language server.";
                        window.showErrorMessage(errorMessage);
                        throw new Error(errorMessage);
                    }

                    console.log(`[gls] ${Constants.GALAXY_LS_PACKAGE} installed successfully.`);
                    if (storageManager.isServerFirstTimeInstall()) {
                        window.showInformationMessage("Galaxy Tools extension is ready!");
                        storageManager.setServerInstalled();
                    }

                    resolve(venvPython);
                } catch (err: any) {
                    window.showErrorMessage(err);
                    console.error(`[gls] installLSWithProgress err: ${err}`);
                    reject(err);
                }
            });
        }
    );
}

function getPythonFromVirtualEnvPath(venvPath: string): string {
    return Constants.IS_WIN
        ? join(venvPath, "Scripts", Constants.PYTHON_WIN)
        : join(venvPath, "bin", Constants.PYTHON_UNIX);
}

function getPythonCrossPlatform(): string {
    return Constants.IS_WIN ? Constants.PYTHON_WIN : Constants.PYTHON_UNIX;
}

function getVirtualEnvironmentPath(extensionDirectory: string, envName: string): string {
    const path = join(extensionDirectory, envName);
    return path;
}

async function isPythonPackageInstalled(python: string, packageName: string, version: string): Promise<boolean> {
    if (!existsSync(python)) {
        console.log(`[gls] Python not found in: ${python}`);
        return false;
    }

    const pattern = /Version: (?<version>\d+.\d+.\d+)/m;
    const getPackageInfoCmd = `"${python}" -m pip show ${packageName}`;
    try {
        const packageInfo = await execAsync(getPackageInfoCmd);
        const match = packageInfo.match(new RegExp(pattern));
        console.log(`[gls] Version found: ${packageName} - ${match?.groups?.version}`);
        return version === match?.groups?.version;
    } catch (err: any) {
        console.error(`[gls] isPythonPackageInstalled err: ${err}`);
        return false;
    }
}

async function installPythonPackage(python: string, packageName: string, version: string): Promise<boolean> {
    const installPipPackageCmd = `"${python}" -m pip install ${packageName}==${version}`;
    try {
        await execAsync(installPipPackageCmd);
        return isPythonPackageInstalled(python, packageName, version);
    } catch (err: any) {
        console.error(`[gls] installPythonPackage err: ${err}`);
        return false;
    }
}

async function getPythonVersion(python: string): Promise<number[]> {
    const getPythonVersionCmd = `"${python}" --version`;
    const version = await execAsync(getPythonVersionCmd);
    const numbers = version.match(new RegExp(/\d/g));
    if (numbers === null) return [0, 0];
    return numbers.map((v) => Number.parseInt(v));
}

async function checkPythonVersion(python: string): Promise<boolean> {
    try {
        const [major, minor] = await getPythonVersion(python);
        return major === 3 && minor >= 8;
    } catch {
        return false;
    }
}

async function getPython(): Promise<string | undefined> {
    let python = workspace.getConfiguration("python").get<string>("pythonPath", getPythonCrossPlatform());
    if (await checkPythonVersion(python)) {
        return python;
    }

    return undefined;
}

async function selectPythonUsingFileDialog(): Promise<string | undefined> {
    let result = await window.showOpenDialog({
        openLabel: "Select",
        canSelectMany: false,
        title: `Select the Python ${Constants.REQUIRED_PYTHON_VERSION} binary:`,
    });

    if (result !== undefined) {
        console.log(`Selected file: ${result[0].fsPath}`);
        const pythonPath = result[0].fsPath;
        if (await checkPythonVersion(pythonPath)) {
            return pythonPath;
        } else {
            window.showErrorMessage(
                `The selected file is not a valid Python ${Constants.REQUIRED_PYTHON_VERSION} path!`
            );
        }
    }

    return undefined;
}

async function createVirtualEnvironment(python: string, name: string, cwd: string): Promise<string> {
    const path = getVirtualEnvironmentPath(cwd, name);
    if (!existsSync(path)) {
        const createVirtualEnvCmd = `"${python}" -m venv ${name}`;
        await execAsync(createVirtualEnvCmd, { cwd });
    }
    return path;
}
