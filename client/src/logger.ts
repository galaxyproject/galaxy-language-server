import { window, OutputChannel } from "vscode";

const outputChannel: OutputChannel = window.createOutputChannel("Galaxy Tools Language Server");

export function logInfo(message: string) {
    outputChannel.appendLine(`[INFO] ${message}`);
}

export function logError(message: string) {
    outputChannel.appendLine(`[ERROR] ${message}`);
}

export function logDebug(message: string) {
    outputChannel.appendLine(`[DEBUG] ${message}`);
}

export function showOutput() {
    outputChannel.show();
}

export { outputChannel };
