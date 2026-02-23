import { gte } from "semver";
import { IPackageManager, InstallationResult } from "./interfaces";
import { VERSION_PATTERN } from "./constants";
import { logger } from "../logger";
import { ExecAsyncFn } from "./types";

/**
 * Base class for package managers with common functionality.
 */
abstract class BasePackageManager implements IPackageManager {
    constructor(protected execAsync: ExecAsyncFn) {}

    abstract install(pythonPath: string, packageName: string, version: string): Promise<InstallationResult>;
    abstract installEditable(pythonPath: string, packagePath: string): Promise<InstallationResult>;
    abstract upgrade(pythonPath: string, packages: string[]): Promise<InstallationResult>;
    abstract getName(): string;

    async isPackageInstalled(pythonPath: string, packageName: string, requiredVersion: string): Promise<boolean> {
        try {
            const getPackageInfoCmd = `"${pythonPath}" -m pip show ${packageName}`;
            const packageInfo = await this.execAsync(getPackageInfoCmd);
            const match = packageInfo.match(VERSION_PATTERN);
            const installedVersion = match?.groups?.version ?? "0.0.0";
            logger.debug(`Package version check: ${packageName} - found ${installedVersion}, required ${requiredVersion}`);
            return gte(installedVersion, requiredVersion);
        } catch (err: any) {
            logger.warn(`Failed to check package version for ${packageName}: ${err}`);
            return false;
        }
    }

    /**
     * Execute a command and return success/failure result.
     */
    protected async executeCommand(command: string, successIndicators: string[]): Promise<InstallationResult> {
        try {
            const output = await this.execAsync(command);
            
            // Check for success indicators
            const success = successIndicators.some(indicator => output.includes(indicator));
            
            if (!success) {
                logger.error(`Command failed - no success indicator found`);
                logger.error(`Output: ${output}`);
                return {
                    success: false,
                    error: "No success indicator in output",
                    output
                };
            }
            
            return {
                success: true,
                output
            };
        } catch (err: any) {
            const errorMessage = err.message || String(err);
            logger.error(`Command execution error: ${errorMessage}`);
            return {
                success: false,
                error: errorMessage
            };
        }
    }
}

/**
 * Package manager implementation using uv (faster alternative to pip).
 */
export class UvPackageManager extends BasePackageManager {
    getName(): string {
        return "uv";
    }

    async install(pythonPath: string, packageName: string, version: string): Promise<InstallationResult> {
        const command = `uv pip install --python "${pythonPath}" ${packageName}==${version}`;
        logger.debug(`Installing ${packageName} with uv: ${command}`);
        
        const result = await this.executeCommand(command, [
            `+ ${packageName}`,
            `~ ${packageName}`,
            "Successfully installed"
        ]);
        
        if (result.success) {
            // Verify installation
            const installed = await this.isPackageInstalled(pythonPath, packageName, version);
            if (!installed) {
                return {
                    success: false,
                    error: "Package installation verification failed",
                    output: result.output
                };
            }
        }
        
        return result;
    }

    async installEditable(pythonPath: string, packagePath: string): Promise<InstallationResult> {
        const command = `uv pip install --python "${pythonPath}" -e ${packagePath}`;
        logger.debug(`Installing editable package with uv: ${command}`);
        
        return this.executeCommand(command, [
            "+ galaxy-language-server",
            "~ galaxy-language-server",
            "Successfully installed",
            "Successfully built"
        ]);
    }

    async upgrade(pythonPath: string, packages: string[]): Promise<InstallationResult> {
        const packageList = packages.join(" ");
        const command = `uv pip install --python "${pythonPath}" --upgrade ${packageList}`;
        logger.debug(`Upgrading packages with uv: ${command}`);
        
        return this.executeCommand(command, [
            "Successfully installed",
            "+ pip",
            "+ setuptools",
            "~ pip",
            "~ setuptools"
        ]);
    }
}

/**
 * Traditional package manager implementation using pip.
 */
export class PipPackageManager extends BasePackageManager {
    getName(): string {
        return "pip";
    }

    async install(pythonPath: string, packageName: string, version: string): Promise<InstallationResult> {
        const command = `"${pythonPath}" -m pip install ${packageName}==${version}`;
        logger.debug(`Installing ${packageName} with pip: ${command}`);
        
        const result = await this.executeCommand(command, [
            "Successfully installed",
            "Successfully built"
        ]);
        
        if (result.success) {
            // Verify installation
            const installed = await this.isPackageInstalled(pythonPath, packageName, version);
            if (!installed) {
                return {
                    success: false,
                    error: "Package installation verification failed",
                    output: result.output
                };
            }
        }
        
        return result;
    }

    async installEditable(pythonPath: string, packagePath: string): Promise<InstallationResult> {
        const command = `"${pythonPath}" -m pip install -e ${packagePath}`;
        logger.debug(`Installing editable package with pip: ${command}`);
        
        return this.executeCommand(command, [
            "Successfully installed",
            "Successfully built"
        ]);
    }

    async upgrade(pythonPath: string, packages: string[]): Promise<InstallationResult> {
        const packageList = packages.join(" ");
        const command = `"${pythonPath}" -m pip install --upgrade ${packageList}`;
        logger.debug(`Upgrading packages with pip: ${command}`);
        
        return this.executeCommand(command, [
            "Successfully installed"
        ]);
    }
}

/**
 * Factory for creating package manager instances.
 * Detects availability of uv and falls back to pip.
 */
export class PackageManagerFactory {
    private static cachedManager: IPackageManager | null = null;

    /**
     * Create a package manager instance.
     * Uses uv if available, otherwise falls back to pip.
     * Results are cached for efficiency.
     */
    static async create(execAsync: ExecAsyncFn): Promise<IPackageManager> {
        if (this.cachedManager) {
            return this.cachedManager;
        }

        // Try to detect uv
        try {
            const uvVersion = await execAsync("uv --version");
            logger.info(`Using uv for faster package management: ${uvVersion.trim()}`);
            this.cachedManager = new UvPackageManager(execAsync);
        } catch {
            logger.debug("uv not available, falling back to pip");
            this.cachedManager = new PipPackageManager(execAsync);
        }

        return this.cachedManager;
    }

    /**
     * Clear cached manager (useful for testing).
     */
    static clearCache(): void {
        this.cachedManager = null;
    }
}
