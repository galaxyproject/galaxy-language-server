interface VersionInfo {
    major: number;
    minor: number;
    patch: number;
}

/**
 * Core interfaces for the Python environment setup system.
 * These interfaces enable dependency injection and testability.
 */

/**
 * Result of attempting to discover or validate a Python installation.
 */
export interface PythonDiscoveryResult {
    /**
     * Path to the Python executable if found and valid.
     */
    pythonPath?: string;
    
    /**
     * Whether the discovery/validation was successful.
     */
    success: boolean;
    
    /**
     * Error message if discovery/validation failed.
     */
    error?: string;
    
    /**
     * Python version information if available.
     */
    version?: VersionInfo;
}

/**
 * Result of a package installation operation.
 */
export interface InstallationResult {
    /**
     * Whether the installation succeeded.
     */
    success: boolean;
    
    /**
     * Error message if installation failed.
     */
    error?: string;
    
    /**
     * Output from the installation command.
     */
    output?: string;
}

/**
 * Information about a Python environment.
 */
export interface EnvironmentInfo {
    /**
     * Path to the virtual environment directory.
     */
    path: string;
    
    /**
     * Path to the Python executable within the environment.
     */
    pythonPath: string;
    
    /**
     * Whether the environment exists and is valid.
     */
    exists: boolean;
    
    /**
     * Python version in the environment.
     */
    version?: VersionInfo;
}

/**
 * Interface for package manager implementations (pip, uv).
 */
export interface IPackageManager {
    /**
     * Install a Python package at a specific version.
     * @param pythonPath Path to the Python executable
     * @param packageName Name of the package to install
     * @param version Version to install
     * @returns Installation result
     */
    install(pythonPath: string, packageName: string, version: string): Promise<InstallationResult>;
    
    /**
     * Install a package in editable mode from a local path.
     * @param pythonPath Path to the Python executable
     * @param packagePath Path to the package source
     * @returns Installation result
     */
    installEditable(pythonPath: string, packagePath: string): Promise<InstallationResult>;
    
    /**
     * Upgrade packages in the environment.
     * @param pythonPath Path to the Python executable
     * @param packages Array of package names to upgrade
     * @returns Installation result
     */
    upgrade(pythonPath: string, packages: string[]): Promise<InstallationResult>;
    
    /**
     * Check if a package is installed at the required version.
     * @param pythonPath Path to the Python executable
     * @param packageName Name of the package
     * @param requiredVersion Minimum required version
     * @returns True if package is installed at or above required version
     */
    isPackageInstalled(pythonPath: string, packageName: string, requiredVersion: string): Promise<boolean>;
    
    /**
     * Get the name of this package manager.
     */
    getName(): string;
}

/**
 * Interface for Python discovery and validation.
 */
export interface IPythonFinder {
    /**
     * Find a suitable Python installation.
     * Checks configured Python path and prompts user if needed.
     * @param storedPythonPath Previously stored Python path, if any
     * @param silentMode If true, don't show UI prompts
     * @returns Discovery result
     */
    findPython(storedPythonPath?: string | null, silentMode?: boolean): Promise<PythonDiscoveryResult>;
    
    /**
     * Validate a Python installation meets requirements.
     * @param pythonPath Path to Python executable to validate
     * @returns Discovery result with validation details
     */
    validatePython(pythonPath: string): Promise<PythonDiscoveryResult>;
    
    /**
     * Get version information from a Python executable.
     * @param pythonPath Path to Python executable
     * @returns Version array [major, minor, patch] or undefined if failed
     */
    getVersion(pythonPath: string): Promise<number[] | undefined>;
    
    /**
     * Prompt user to select Python using file dialog.
     * @returns Selected Python path or undefined if cancelled
     */
    promptUserForPython(): Promise<string | undefined>;
}

/**
 * Interface for Python virtual environment management.
 */
export interface IPythonEnvironment {
    /**
     * Create a new virtual environment.
     * @param basePython Path to base Python executable
     * @param name Name for the virtual environment
     * @param cwd Working directory where environment will be created
     * @returns Path to created environment
     */
    create(basePython: string, name: string, cwd: string): Promise<string>;
    
    /**
     * Check if the environment exists and is valid.
     * @returns True if environment exists
     */
    exists(): boolean;
    
    /**
     * Get the path to the Python executable in this environment.
     * @returns Path to Python executable
     */
    getPythonPath(): string;
    
    /**
     * Get the path to the virtual environment directory.
     * @returns Environment directory path
     */
    getEnvironmentPath(): string;
    
    /**
     * Upgrade core packages in the environment (pip, setuptools).
     * @returns Installation result
     */
    upgrade(): Promise<InstallationResult>;
    
    /**
     * Get information about this environment.
     * @returns Environment information
     */
    getInfo(): EnvironmentInfo;
}

/**
 * Custom error for Python-related issues.
 */
export class PythonNotFoundError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'PythonNotFoundError';
    }
}

/**
 * Custom error for installation issues.
 */
export class InstallationError extends Error {
    constructor(message: string, public readonly details?: string) {
        super(message);
        this.name = 'InstallationError';
    }
}

/**
 * Custom error for version mismatch issues.
 */
export class VersionMismatchError extends Error {
    constructor(
        message: string,
        public readonly requiredVersion: string,
        public readonly foundVersion?: string
    ) {
        super(message);
        this.name = 'VersionMismatchError';
    }
}