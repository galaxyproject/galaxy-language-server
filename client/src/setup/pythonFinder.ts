import {  workspace } from "vscode";
import { IPythonFinder, PythonDiscoveryResult } from "./interfaces";
import { ERROR_MESSAGES } from "./constants";
import { logger } from "../logger";
import { Constants } from "../constants";
import { ExecAsyncFn } from "./types";

/**
 * Service for discovering and validating Python installations.
 */
export class PythonFinder implements IPythonFinder {
    constructor(private execAsync: ExecAsyncFn) { }

    async findPython(storedPythonPath?: string | null): Promise<PythonDiscoveryResult> {
        // Try stored Python path first
        if (storedPythonPath) {
            logger.debug(`Checking stored Python path: ${storedPythonPath}`);
            const result = await this.validatePython(storedPythonPath);
            if (result.success) {
                logger.info(`Using stored Python: ${storedPythonPath}`);
                return result;
            } else {
                logger.warn("Stored Python is no longer valid");
            }
        }

        // Try configured Python path
        const configuredPython = workspace.getConfiguration("python").get<string>("pythonPath", this.getPythonCrossPlatform());
        logger.debug(`Checking configured Python: ${configuredPython}`);
        const configResult = await this.validatePython(configuredPython);
        if (configResult.success) {
            logger.info(`Using configured Python: ${configuredPython}`);
            return configResult;
        }

        return {
            success: false,
            error: ERROR_MESSAGES.PYTHON_REQUIRED(Constants.REQUIRED_PYTHON_VERSION)
        };
    }

    async validatePython(pythonPath: string): Promise<PythonDiscoveryResult> {
        try {
            const version = await this.getVersion(pythonPath);

            if (!version) {
                return {
                    success: false,
                    error: ERROR_MESSAGES.VERSION_CHECK_FAILED,
                    pythonPath
                };
            }

            const [major, minor, patch] = version;

            // Check version requirements (Python 3.8+)
            if (major === 3 && minor >= 8) {
                return {
                    success: true,
                    pythonPath,
                    version: { major, minor, patch }
                };
            } else {
                return {
                    success: false,
                    error: `Python version ${major}.${minor}.${patch} does not meet requirements (3.8+)`,
                    pythonPath,
                    version: { major, minor, patch }
                };
            }
        } catch (err: any) {
            logger.warn(`Python validation failed for ${pythonPath}: ${err}`);
            return {
                success: false,
                error: err.message || ERROR_MESSAGES.VERSION_CHECK_FAILED,
                pythonPath
            };
        }
    }

    async getVersion(pythonPath: string): Promise<number[] | undefined> {
        try {
            const getPythonVersionCmd = `"${pythonPath}" --version`;
            const version = await this.execAsync(getPythonVersionCmd);
            logger.debug(`Python version found: ${version}`);

            const numbers = version.match(/\d+/g);
            if (numbers === null || numbers.length < 2) {
                return undefined;
            }

            return numbers.map((v) => Number.parseInt(v, 10));
        } catch (err: any) {
            logger.warn(`Failed to get Python version from ${pythonPath}: ${err}`);
            return undefined;
        }
    }

    /**
     * Get platform-specific Python command name.
     */
    private getPythonCrossPlatform(): string {
        return Constants.IS_WIN ? Constants.PYTHON_WIN : Constants.PYTHON_UNIX;
    }
}
