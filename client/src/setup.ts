import { join } from "path";
import { existsSync } from "fs";
import { ExtensionContext, ProgressLocation, window, workspace } from "vscode";
import { IS_WIN, LS_VENV_NAME, LS_VENV_PATH, GALAXY_LS_PACKAGE } from "./constants";
import { execAsync } from "./utils";

export function getPythonFromVenvPath(venvPath: string = LS_VENV_PATH): string {
    return IS_WIN ? join(venvPath, "Scripts", "python") : join(venvPath, "bin", "python");
}

async function isPythonPackageInstalled(python: string, packageName: string): Promise<boolean> {
    let listPipPackagesCmd = `"${python}" -m pip show ${packageName}`;

    console.log(`[gls] listPipPackagesCmd: ${listPipPackagesCmd}`);

    try {
        const packageInfo = await execAsync(listPipPackagesCmd);

        console.log(`[gls] packageInfo: ${packageInfo}`);

        const packageVersion = packageInfo.match(new RegExp(/Version: \d+\.\d+\.\d+/g));

        console.log(`[gls] packageVersion: ${packageVersion}`);

        return packageVersion !== null;
    } catch (err) {
        console.log(`[gls] isPythonPackageInstalled err: ${err}`);
        return false;
    }
}

async function intallPythonPackage(python: string, packageName: string): Promise<boolean> {
    const installPipPackageCmd = `"${python}" -m pip install ${packageName}`;
    try {
        const packageInfo = await execAsync(installPipPackageCmd);
        return true
    } catch (err) {
        window.showErrorMessage(err);

        return false;
    }
}

function getPythonCrossPlatform(): string {
    return IS_WIN ? "python" : "python3";
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

export async function getPython(): Promise<string> {
    let python = workspace.getConfiguration("python").get<string>("pythonPath", getPythonCrossPlatform());
    if (await checkPythonVersion(python)) {
        return python;
    }

    let result = await window.showInputBox({
        ignoreFocusOut: true,
        placeHolder: "Enter a path to the python 3.8+.",
        prompt: "This python will be used to create a virtual environment inside the extension directory.",
        validateInput: async (value: string) => {
            if (await checkPythonVersion(value)) {
                return null;
            } else {
                return "Not a valid python path!";
            }
        },
    });

    // User canceled the input
    if (result === "undefined") {
        throw new Error("Python 3.8+ is required!");
    }

    return result as string;
}

async function createVirtualEnvironment(python: string, name: string, cwd: string): Promise<string> {
    const path = join(cwd, name);
    if (!existsSync(path)) {
        const createVenvCmd = `"${python}" -m venv ${name}`;
        await execAsync(createVenvCmd, { cwd });
    }
    return path;
}

export async function installLSWithProgress(context: ExtensionContext): Promise<string> {
    // Check if LS is already installed
    let venvPython = getPythonFromVenvPath();
    const isServerPackageInstalled = await isPythonPackageInstalled(venvPython, GALAXY_LS_PACKAGE);

    if (isServerPackageInstalled) {
        return Promise.resolve(venvPython);
    }

    // Install with progress bar
    return window.withProgress({
        location: ProgressLocation.Notification,
    }, (progress): Promise<string> => {
        return new Promise<string>(async (resolve, reject) => {
            try {
                progress.report({ message: "Installing Galaxy language server..." });

                // Get python interpreter
                const python = await getPython();

                // Create virtual environment
                const venv = await createVirtualEnvironment(python, LS_VENV_NAME, context.extensionPath);

                // Install language server package
                venvPython = getPythonFromVenvPath(venv);
                const isInstalled = await intallPythonPackage(venvPython, GALAXY_LS_PACKAGE)
                if (!isInstalled) {
                    const errorMessage = "There was a problem trying to install the Galaxy language server.";
                    window.showErrorMessage(errorMessage);
                    throw new Error(errorMessage);
                }

                window.showInformationMessage("Galaxy Tools extension is ready!");
                resolve(venvPython);
            } catch (err) {
                window.showErrorMessage(err);
                reject(err);
            }
        });
    });
}
