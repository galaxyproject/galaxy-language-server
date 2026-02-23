/**
 * Shared type definitions for the setup system.
 */

/**
 * Type for async command execution function.
 * Used for dependency injection to allow testing and flexibility.
 */
export type ExecAsyncFn = (command: string, options?: any) => Promise<string>;
