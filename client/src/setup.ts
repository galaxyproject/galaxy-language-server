import { join } from "path";
import { existsSync } from "fs";
import { commands, ExtensionContext, ProgressLocation, Uri, window, workspace } from "vscode";
import { IS_WIN, LS_VENV_NAME, GALAXY_LS_PACKAGE, PYTHON_UNIX, PYTHON_WIN, GALAXY_LS_VERSION, REQUIRED_PYTHON_VERSION } from "./constants";
import { execAsync } from "./utils";

/**
 * Ensures that the Language server is installed in the extension's virtual environment
 * and returns the Python path of the virtual environment or undefined if there was
 * a problem or the user cancelled the installation.
 * @param context The extension context
 */
export async function installLanguageServer(context: ExtensionContext): Promise<string | undefined> {
    // Check if the LS is already installed
    let venvPath = getVirtualEnvironmentPath(context.extensionPath, LS_VENV_NAME)
    if (existsSync(venvPath)) {
        const venvPython = getPythonFromVenvPath(venvPath);
        const isInstalled = await isPythonPackageInstalled(venvPython, GALAXY_LS_PACKAGE, GALAXY_LS_VERSION);
        if (isInstalled) {
            console.log(`[gls] ${GALAXY_LS_PACKAGE} already installed.`);
            return Promise.resolve(venvPython);
        }
    }

    const result = await window.showInformationMessage(`Galaxy Tools needs to install the Galaxy Language Server Python package to continue. This will be installed in a virtual environment inside the extension and will require Python ${REQUIRED_PYTHON_VERSION}`, ...['Install', 'More Info']);

    if (result === undefined) {
        console.log(`[gls] Language server installation cancelled by the user.`);
        return undefined;
    } else if (result === "More Info") {
        commands.executeCommand('vscode.open', Uri.parse('https://github.com/galaxyproject/galaxy-language-server/blob/master/client/README.md#installation'));
    }

    // Install with progress
    return window.withProgress({
        location: ProgressLocation.Window,
        title: "Installing Galaxy language server..."
    }, (progress): Promise<string> => {
        return new Promise<string>(async (resolve, reject) => {
            try {

                if (!existsSync(venvPath)) {
                    console.log(`[gls] Checking Python version...`);
                    let python = await getPython();

                    if (python === undefined) {
                        await window.showInformationMessage(
                            `Please select your Python ${REQUIRED_PYTHON_VERSION} path to continue the installation. This python will be used to create a virtual environment inside the extension directory.`,
                            ...['Select']);
                        python = await selectPythonUsingFileDialog();
                        // User canceled the input
                        if (python === undefined) {
                            const message = `Python ${REQUIRED_PYTHON_VERSION} is required in order to use the language server features.`;
                            window.showErrorMessage(message);
                            throw new Error(message);
                        }
                    }

                    console.log(`[gls] Creating virtual environment...`);
                    venvPath = await createVirtualEnvironment(python, LS_VENV_NAME, context.extensionPath);
                }

                const venvPython = getPythonFromVenvPath(venvPath);
                console.log(`[gls] Using Python from: ${venvPython}`);

                console.log(`[gls] Installing ${GALAXY_LS_PACKAGE}...`);
                const isInstalled = await intallPythonPackage(venvPython, GALAXY_LS_PACKAGE, GALAXY_LS_VERSION)

                if (!isInstalled) {
                    const errorMessage = "There was a problem trying to install the Galaxy language server.";
                    window.showErrorMessage(errorMessage);
                    throw new Error(errorMessage);
                }

                console.log(`[gls] ${GALAXY_LS_PACKAGE} installed successfully.`);
                window.showInformationMessage("Galaxy Tools extension is ready!");
                resolve(venvPython);
            } catch (err) {
                window.showErrorMessage(err);
                console.error(`[gls] installLSWithProgress err: ${err}`);
                reject(err);
            }
        });
    });
}

function getPythonFromVenvPath(venvPath: string): string {
    return IS_WIN ? join(venvPath, "Scripts", PYTHON_WIN) : join(venvPath, "bin", PYTHON_UNIX);
}

function getPythonCrossPlatform(): string {
    return IS_WIN ? PYTHON_WIN : PYTHON_UNIX;
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
    const getPacakgeInfoCmd = `"${python}" -m pip show ${packageName}`;
    try {
        const packageInfo = await execAsync(getPacakgeInfoCmd);
        const match = packageInfo.match(new RegExp(pattern));
        console.log(`[gls] Version found: ${packageName} - ${match?.groups?.version}`);
        return version === match?.groups?.version;
    } catch (err) {
        console.error(`[gls] isPythonPackageInstalled err: ${err}`);
        return false;
    }
}

async function intallPythonPackage(python: string, packageName: string, version: string): Promise<boolean> {
    const installPipPackageCmd = `"${python}" -m pip install ${packageName}==${version}`;
    try {
        await execAsync(installPipPackageCmd);
        return isPythonPackageInstalled(python, packageName, version);
    } catch (err) {
        console.error(`[gls] intallPythonPackage err: ${err}`);
        return false;
    }
}

async function getPythonVersion(python: string): Promise<number[]> {
    const getPythonVersionCmd = `"${python}" --version`;
    const version = await execAsync(getPythonVersionCmd);
    const numbers = version.match(new RegExp(/\d/g));
    if (numbers === null) return [0, 0];
    return numbers.map(v => Number.parseInt(v));
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
        openLabel: "Select", canSelectMany: false,
        title: `Select the Python ${REQUIRED_PYTHON_VERSION} binary:`
    });

    if (result !== undefined) {
        console.log(`Selected file: ${result[0].fsPath}`);
        const pythonPath = result[0].fsPath;
        if (await checkPythonVersion(pythonPath)) {
            return pythonPath;
        } else {
            window.showErrorMessage(`The selected file is not a valid Python ${REQUIRED_PYTHON_VERSION} path!`);
        }
    }

    return undefined;
}

async function createVirtualEnvironment(python: string, name: string, cwd: string): Promise<string> {
    const path = getVirtualEnvironmentPath(cwd, name);
    if (!existsSync(path)) {
        const createVenvCmd = `"${python}" -m venv ${name}`;
        await execAsync(createVenvCmd, { cwd });
    }
    return path;
}
