import { existsSync } from "fs";
import { join } from "path";
import { IPythonEnvironment, IPackageManager, EnvironmentInfo, InstallationResult } from "./interfaces";
import { ERROR_MESSAGES } from "./constants";
import { logger } from "../logger";
import { Constants } from "../constants";
import { ExecAsyncFn } from "./types";

/**
 * Represents and manages a Python virtual environment.
 */
export class PythonEnvironment implements IPythonEnvironment {
    private readonly environmentPath: string;
    private readonly pythonPath: string;

    constructor(
        environmentPath: string,
        private packageManager: IPackageManager,
        private execAsync: ExecAsyncFn
    ) {
        this.environmentPath = environmentPath;
        this.pythonPath = this.computePythonPath(environmentPath);
    }

    async create(basePython: string, name: string, cwd: string): Promise<string> {
        const path = join(cwd, name);

        if (existsSync(path)) {
            logger.info(`Virtual environment already exists at: ${path}`);
            return path;
        }

        logger.info(`Creating virtual environment at: ${path}`);

        // Try using uv first if available (faster and more reliable)
        if (this.packageManager.getName() === "uv") {
            try {
                const createVirtualEnvCmd = `uv venv ${name} --python "${basePython}"`;
                await this.execAsync(createVirtualEnvCmd, { cwd });
                logger.info("Virtual environment created successfully with uv");
                return path;
            } catch (err: any) {
                logger.warn(`Failed to create venv with uv, falling back to python -m venv: ${err.message}`);
            }
        }

        // Fallback to traditional python -m venv
        let venvError = "";
        try {
            const createVirtualEnvCmd = `"${basePython}" -m venv ${name}`;
            await this.execAsync(createVirtualEnvCmd, { cwd });
            logger.info("Virtual environment created successfully");
            return path;
        } catch (err: any) {
            venvError = err.message || String(err);
            logger.warn(`Standard venv creation failed, trying --without-pip fallback: ${venvError}`);
        }

        // Last resort: --without-pip works with uv-managed Python where ensurepip is unavailable
        try {
            const createVirtualEnvWithoutPipCmd = `"${basePython}" -m venv ${name} --without-pip`;
            await this.execAsync(createVirtualEnvWithoutPipCmd, { cwd });
        } catch (fallbackErr: any) {
            logger.error(`Failed to create virtual environment (--without-pip also failed): ${fallbackErr.message || fallbackErr}`);
            throw new Error(`${ERROR_MESSAGES.ENVIRONMENT_CREATION_FAILED}: ${venvError}`);
        }

        logger.info("Virtual environment created successfully (--without-pip)");

        if (this.packageManager.getName() !== "uv") {
            // pip cannot be used inside a venv that was created without pip; fail with actionable message
            const message = ERROR_MESSAGES.VENV_NO_PIP_WITH_PIP_MANAGER;
            logger.error(message);
            throw new Error(message);
        }

        logger.warn("Virtual environment created without pip. uv will be used for package management.");
        return path;
    }

    exists(): boolean {
        return existsSync(this.pythonPath);
    }

    async isHealthy(): Promise<boolean> {
        if (!this.exists()) {
            return false;
        }
        try {
            await this.execAsync(`"${this.pythonPath}" --version`);
            return true;
        } catch {
            return false;
        }
    }

    getPythonPath(): string {
        return this.pythonPath;
    }

    getEnvironmentPath(): string {
        return this.environmentPath;
    }

    async upgrade(): Promise<InstallationResult> {
        logger.info("Upgrading virtual environment dependencies...");

        const result = await this.packageManager.upgrade(this.pythonPath, ["pip", "setuptools"]);

        if (result.success) {
            logger.debug("Virtual environment dependencies upgraded successfully");
        } else {
            logger.warn(`Failed to upgrade virtual environment dependencies: ${result.error}`);
        }

        return result;
    }

    getInfo(): EnvironmentInfo {
        return {
            path: this.environmentPath,
            pythonPath: this.pythonPath,
            exists: this.exists()
        };
    }

    /**
     * Compute the path to Python executable based on environment path and platform.
     */
    private computePythonPath(envPath: string): string {
        return Constants.IS_WIN
            ? join(envPath, "Scripts", Constants.PYTHON_WIN)
            : join(envPath, "bin", Constants.PYTHON_UNIX);
    }

    /**
     * Factory method to create a PythonEnvironment instance.
     */
    static create(
        extensionDirectory: string,
        envName: string,
        packageManager: IPackageManager,
        execAsync: ExecAsyncFn
    ): PythonEnvironment {
        const environmentPath = join(extensionDirectory, envName);
        return new PythonEnvironment(environmentPath, packageManager, execAsync);
    }
}
