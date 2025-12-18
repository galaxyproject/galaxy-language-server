import { window, OutputChannel } from "vscode";

/**
 * Interface for logging operations
 */
export interface ILogger {
    /**
     * Log an informational message
     * @param message The message to log
     */
    info(message: string): void;
    /**
     * Log an error message
     * @param message The error message to log
     */
    error(message: string): void;
    /**
     * Log a warning message
     * @param message The warning message to log
     */
    warn(message: string): void;
    /**
     * Log a debug message
     * @param message The debug message to log
     */
    debug(message: string): void;
    /**
     * Show the output channel in the VS Code UI
     */
    show(): void;
    /**
     * Append a raw message without any prefix
     * Useful for messages that should not be prefixed
     * @param message The message to append
     */
    appendLine(message: string): void;
}

/**
 * Logger implementation using VS Code OutputChannel
 */
class Logger implements ILogger {
    private outputChannel: OutputChannel;

    constructor(channelName: string) {
        this.outputChannel = window.createOutputChannel(channelName);
    }

    info(message: string): void {
        const timestamp = this.getTimestamp();
        this.outputChannel.appendLine(`[${timestamp}] [INFO] ${message}`);
    }

    error(message: string): void {
        const timestamp = this.getTimestamp();
        this.outputChannel.appendLine(`[${timestamp}] [ERROR] ${message}`);
    }

    warn(message: string): void {
        const timestamp = this.getTimestamp();
        this.outputChannel.appendLine(`[${timestamp}] [WARN] ${message}`);
    }

    debug(message: string): void {
        const timestamp = this.getTimestamp();
        this.outputChannel.appendLine(`[${timestamp}] [DEBUG] ${message}`);
    }

    show(): void {
        this.outputChannel.show();
    }

    appendLine(message: string): void {
        this.outputChannel.appendLine(message);
    }

    /**
     * Get the underlying OutputChannel for compatibility
     */
    getOutputChannel(): OutputChannel {
        return this.outputChannel;
    }

    /**
     * Get a formatted timestamp string for log entries
     * @returns Timestamp in HH:MM:SS.mmm format
     */
    private getTimestamp(): string {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const seconds = now.getSeconds().toString().padStart(2, '0');
        const milliseconds = now.getMilliseconds().toString().padStart(3, '0');
        return `${hours}:${minutes}:${seconds}.${milliseconds}`;
    }
}

// Create and export the logger instance
export const logger: ILogger = new Logger("Galaxy Tools Language Server");

// Export the raw output channel for backward compatibility
export const outputChannel: OutputChannel = (logger as Logger).getOutputChannel();
