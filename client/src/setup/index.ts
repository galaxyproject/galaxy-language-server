/**
 * Public API for the Python environment setup system.
 * 
 * This module provides the main entry points for installing and managing
 * the Galaxy Language Server Python package in a virtual environment.
 */

// Export main installation functions
export { installLanguageServer, silentInstallLanguageServerForTesting } from "./main";

// Export types
export type { ExecAsyncFn } from "./types";

// Export interfaces for external use
export type {
    IPackageManager,
    IPythonFinder,
    IPythonEnvironment,
    PythonDiscoveryResult,
    InstallationResult,
    EnvironmentInfo
} from "./interfaces";

// Export custom errors
export {
    PythonNotFoundError,
    InstallationError,
    VersionMismatchError
} from "./interfaces";

// Export factory classes for advanced usage
export { PackageManagerFactory } from "./packageManager";
export { PythonFinder } from "./pythonFinder";
export { PythonEnvironment } from "./pythonEnvironment";
