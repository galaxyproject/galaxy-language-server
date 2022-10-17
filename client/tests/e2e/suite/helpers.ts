import * as vscode from "vscode";
import * as path from "path";
import * as assert from "assert";
import { silentInstallLanguageServerForTesting } from "../../../src/setup";

/**
 * Contains the document and its corresponding editor
 */
export interface DocumentEditor {
    editor: vscode.TextEditor;
    document: vscode.TextDocument;
}

export async function activate(): Promise<unknown> {
    const ext = vscode.extensions.getExtension("davelopez.galaxy-language-server");
    const api = ext?.isActive ? ext.exports : await ext?.activate();
    return api;
}

export async function ensureGalaxyLanguageServerInstalled(): Promise<string | undefined> {
    const installDir = path.join(__dirname, "..", "..", "..", "..");
    const result = await silentInstallLanguageServerForTesting(installDir);
    return result;
}

export async function openDocumentInEditor(docUri: vscode.Uri): Promise<DocumentEditor> {
    const document = await vscode.workspace.openTextDocument(docUri);
    const editor = await vscode.window.showTextDocument(document);
    return {
        editor,
        document,
    };
}

export async function openDocument(docUri: vscode.Uri): Promise<vscode.TextDocument> {
    const document = await vscode.workspace.openTextDocument(docUri);

    return document;
}

export async function activateAndOpenInEditor(docUri: vscode.Uri): Promise<DocumentEditor> {
    await activate();
    return openDocumentInEditor(docUri);
}

export async function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function waitForDiagnostics(docUri: vscode.Uri, timeoutInMilliseconds: number = 2000): Promise<void> {
    const waitMilliseconds = 100;
    let waitTimeout = timeoutInMilliseconds;
    let diagnostics = vscode.languages.getDiagnostics(docUri);
    while (waitTimeout > 0 && !diagnostics.length) {
        await sleep(waitMilliseconds);
        waitTimeout -= waitMilliseconds;
        diagnostics = vscode.languages.getDiagnostics(docUri);
    }
}

export const getDocPath = (filePath: string): string => {
    return path.resolve(
        __dirname,
        path.join("..", "..", "..", "..", "..", "server", "galaxyls", "tests", "files", filePath)
    );
};

export const getDocUri = (filePath: string): vscode.Uri => {
    return vscode.Uri.file(getDocPath(filePath));
};

export async function assertDiagnostics(docUri: vscode.Uri, expectedDiagnostics: vscode.Diagnostic[]): Promise<void> {
    const actualDiagnostics = vscode.languages.getDiagnostics(docUri);

    assert.equal(actualDiagnostics.length, expectedDiagnostics.length);

    expectedDiagnostics.forEach((expectedDiagnostic, i) => {
        const actualDiagnostic = actualDiagnostics[i];
        assert.equal(
            actualDiagnostic.message,
            expectedDiagnostic.message,
            `On diagnostic: ${actualDiagnostic.message}`
        );
        assert.deepEqual(
            actualDiagnostic.range,
            expectedDiagnostic.range,
            `On diagnostic: ${actualDiagnostic.message}`
        );
        assert.equal(
            actualDiagnostic.severity,
            expectedDiagnostic.severity,
            `On diagnostic: ${actualDiagnostic.message}`
        );
    });
}

/**
 * Asserts that the given workflow document has no diagnostics i.e. is valid.
 * @param docUri Workflow document URI
 */
export async function assertValid(docUri: vscode.Uri): Promise<void> {
    const actualDiagnostics = vscode.languages.getDiagnostics(docUri);
    assert.equal(actualDiagnostics.length, 0);
}

export function closeAllEditors(): Thenable<unknown> {
    return vscode.commands.executeCommand("workbench.action.closeAllEditors");
}
