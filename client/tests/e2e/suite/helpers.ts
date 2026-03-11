import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";
import * as os from "os";
import * as assert from "assert";
import { silentInstallLanguageServerForTesting } from "../../../src/setup";
import { Constants } from "../../../src/constants";

/**
 * Contains the document and its corresponding editor
 */
export interface DocumentEditor {
    editor: vscode.TextEditor;
    document: vscode.TextDocument;
}

let activationPromise: Promise<unknown> | null = null;

export async function activate(): Promise<unknown> {
    if (!activationPromise) {
        activationPromise = activateExtension();
    }
    return activationPromise;
}

let installPromise: Promise<string | undefined> | null = null;

export async function ensureGalaxyLanguageServerInstalled(): Promise<string | undefined> {
    if (!installPromise) {
        const installDir = path.join(__dirname, "..", "..", "..", "..");
        installPromise = silentInstallLanguageServerForTesting(installDir);
    }
    return installPromise;
}

export async function openDocumentInEditor(docUri: vscode.Uri): Promise<DocumentEditor> {
    const document = await vscode.workspace.openTextDocument(docUri);
    const editor = await vscode.window.showTextDocument(document);
    return {
        editor,
        document,
    };
}

export async function activateAndOpenInEditor(docUri: vscode.Uri): Promise<DocumentEditor> {
    await activate();
    return openDocumentInEditor(docUri);
}

/**
 * Opens a committed fixture file in an editor.
 */
export async function openFixtureInEditor(filePath: string): Promise<DocumentEditor> {
    const docUri = getDocUri(filePath);
    return activateAndOpenInEditor(docUri);
}

/**
 * Opens a committed fixture file and waits until diagnostics are reported.
 * Returns the document/editor for further assertions.
 */
export async function openFixtureAndWaitForDiagnostics(
    filePath: string,
    timeoutInMilliseconds: number = 5000
): Promise<DocumentEditor> {
    const docUri = getDocUri(filePath);
    const docEditor = await activateAndOpenInEditor(docUri);
    await waitForDiagnostics(docUri, timeoutInMilliseconds);
    return docEditor;
}

/**
 * Opens a committed fixture file and waits until diagnostics settle, even if empty.
 * Use for valid documents that may return no diagnostics.
 */
export async function openFixtureAndWaitForDiagnosticsToSettle(
    filePath: string,
    timeoutInMilliseconds: number = 5000
): Promise<DocumentEditor> {
    const docUri = getDocUri(filePath);
    return openAndWaitForDiagnosticsToSettle(docUri, timeoutInMilliseconds);
}

export async function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => resolveAfterDelay(ms, resolve));
}

/**
 * Waits until at least one diagnostic is reported for the given URI, or until
 * the timeout elapses. Uses VS Code's onDidChangeDiagnostics event so it reacts
 * immediately rather than polling.
 */
function waitForDiagnosticsChange(
    docUri: vscode.Uri,
    timeoutInMilliseconds: number,
    predicate: () => boolean = alwaysTrue
): Promise<void> {
    return new DiagnosticsWaiter(docUri, timeoutInMilliseconds, predicate).wait();
}

export async function waitForDiagnostics(docUri: vscode.Uri, timeoutInMilliseconds: number = 5000): Promise<void> {
    if (hasDiagnosticsForUri(docUri)) {
        return;
    }
    const predicate = createHasDiagnosticsPredicate(docUri);
    await waitForDiagnosticsChange(docUri, timeoutInMilliseconds, predicate);
}

/**
 * Opens a document in an editor and waits until the language server publishes
 * any diagnostics result for it — including an empty array (valid document).
 *
 * The event listener is registered BEFORE the document is opened so that the
 * server's publishDiagnostics response is never missed regardless of how fast
 * the language server responds.
 *
 * Use this instead of `activateAndOpenInEditor` + `waitForDiagnostics` when
 * the document is expected to be valid and produce no diagnostics.
 */
export async function openAndWaitForDiagnosticsToSettle(
    docUri: vscode.Uri,
    timeoutInMilliseconds: number = 5000
): Promise<DocumentEditor> {
    await activate();
    // Register the listener BEFORE opening so we never miss the event.
    const settled = waitForDiagnosticsChange(docUri, timeoutInMilliseconds);
    const docEditor = await openDocumentInEditor(docUri);
    await settled;
    return docEditor;
}

/**
 * Tracks temp .xml files created during tests so they can be cleaned up after
 * each test by calling deleteTempDocuments().
 */
const tempFilePaths: string[] = [];

/**
 * Creates a real .xml temp file with the given content, sets the language to
 * galaxytool, and opens it in an editor. The file is tracked for automatic
 * cleanup by deleteTempDocuments() / teardownTest().
 *
 * Use this for any test that needs to EDIT and SAVE a document.
 */
export async function openTempDocumentInEditor(content: string): Promise<DocumentEditor> {
    await activate();
    const tmpFile = path.join(
        os.tmpdir(),
        `gls-test-${Date.now()}-${Math.random().toString(36).slice(2)}.xml`
    );
    fs.writeFileSync(tmpFile, content, "utf-8");
    tempFilePaths.push(tmpFile);
    const docUri = vscode.Uri.file(tmpFile);
    const document = await vscode.workspace.openTextDocument(docUri);
    await vscode.languages.setTextDocumentLanguage(document, Constants.LANGUAGE_ID);
    const editor = await vscode.window.showTextDocument(document);
    return { editor, document };
}

/**
 * Deletes all temp files registered by openTempDocumentInEditor().
 * Call this in teardown via teardownTest().
 */
export function deleteTempDocuments(): void {
    while (tempFilePaths.length > 0) {
        const filePath = tempFilePaths.pop()!;
        try { fs.unlinkSync(filePath); } catch { /* already gone */ }
    }
}

/**
 * Forces the language server to (re-)validate the document via did_save.
 * Inserts a single trailing space so VS Code always marks the document dirty
 * (replacing with identical content is a no-op and won't fire did_save).
 * Then saves the document and waits for diagnostics to appear.
 */
export async function triggerValidationOnSave(
    editor: vscode.TextEditor,
    docUri: vscode.Uri,
    timeout = 5000
): Promise<void> {
    const document = editor.document;
    const endPos = document.positionAt(document.getText().length);
    // Insert a trailing space to guarantee the document is marked dirty,
    // regardless of current content. Without a real change, VS Code may
    // skip the save and not fire did_save to the language server.
    const predicate = createHasDiagnosticsPredicate(docUri);
    const settled = waitForDiagnosticsChange(docUri, timeout, predicate);
    await editor.edit(createInsertTrailingSpaceCallback(endPos));
    await document.save();
    await settled;
}

export function getDocPath(filePath: string): string {
    return path.resolve(
        __dirname,
        path.join("..", "..", "..", "..", "..", "server", "galaxyls", "tests", "files", filePath)
    );
}

export function getDocUri(filePath: string): vscode.Uri {
    return vscode.Uri.file(getDocPath(filePath));
}

export async function assertDiagnostics(docUri: vscode.Uri, expectedDiagnostics: vscode.Diagnostic[]): Promise<void> {
    const actualDiagnostics = vscode.languages.getDiagnostics(docUri);

    assert.equal(actualDiagnostics.length, expectedDiagnostics.length);

    for (let i = 0; i < expectedDiagnostics.length; i += 1) {
        const expectedDiagnostic = expectedDiagnostics[i];
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
    }
}

/**
 * Asserts that the given document has no diagnostics i.e. is valid.
 * @param docUri document URI
 */
export async function assertValid(docUri: vscode.Uri): Promise<void> {
    const actualDiagnostics = vscode.languages.getDiagnostics(docUri);
    assert.equal(actualDiagnostics.length, 0);
}

/**
 * Asserts that there are no error-level diagnostics for the given document.
 */
export function assertHasNoErrors(docUri: vscode.Uri): void {
    const diagnostics = vscode.languages.getDiagnostics(docUri);
    const hasErrors = diagnostics.some((d) => d.severity === vscode.DiagnosticSeverity.Error);
    assert.equal(hasErrors, false, "Document should have no error diagnostics");
}

/**
 * Asserts that at least one error-level diagnostic exists for the given document.
 */
export function assertHasErrors(docUri: vscode.Uri): void {
    const diagnostics = vscode.languages.getDiagnostics(docUri);
    assert.ok(
        diagnostics.some((d) => d.severity === vscode.DiagnosticSeverity.Error),
        "Document should have at least one error diagnostic"
    );
}

/**
 * Asserts that a diagnostic with the given message exists for the document.
 */
export function assertDiagnosticMessageExists(docUri: vscode.Uri, expectedMessage: string): void {
    const diagnostics = vscode.languages.getDiagnostics(docUri);
    assert.ok(
        diagnostics.some((d) => d.message === expectedMessage),
        `Expected to find diagnostic with message: "${expectedMessage}"`
    );
}

/**
 * Returns only error-level diagnostics for the given document.
 */
export function getErrorDiagnostics(docUri: vscode.Uri): vscode.Diagnostic[] {
    const diagnostics = vscode.languages.getDiagnostics(docUri);
    return diagnostics.filter((d) => d.severity === vscode.DiagnosticSeverity.Error);
}

/**
 * Returns only warning-level diagnostics for the given document.
 */
export function getWarningDiagnostics(docUri: vscode.Uri): vscode.Diagnostic[] {
    const diagnostics = vscode.languages.getDiagnostics(docUri);
    return diagnostics.filter((d) => d.severity === vscode.DiagnosticSeverity.Warning);
}

/**
 * Executes a VS Code command and asserts that the result exists and has no error.
 * Returns the command result for further assertions.
 */
export async function executeCommandAndExpectSuccess<T>(command: string, ...args: any[]): Promise<T> {
    const result = await vscode.commands.executeCommand<T>(command, ...args);
    assert.ok(result, `Command "${command}" should return a result`);
    return result;
}

/**
 * Saves a document and waits for diagnostics to settle after the save.
 * Returns the updated diagnostics for the document.
 */
export async function saveAndWaitForDiagnostics(
    document: vscode.TextDocument,
    severityFilter: vscode.DiagnosticSeverity | null = null,
    timeoutInMilliseconds: number = 5000
): Promise<vscode.Diagnostic[]> {
    const settled = waitForDiagnosticsChange(document.uri, timeoutInMilliseconds);
    await document.save();
    await settled;
    let diagnostics = vscode.languages.getDiagnostics(document.uri);
    if (severityFilter !== null) {
        diagnostics = diagnostics.filter((d) => d.severity === severityFilter);
    }
    return diagnostics;
}

export function closeAllEditors(): Thenable<unknown> {
    return vscode.commands.executeCommand("workbench.action.closeAllEditors");
}

/**
 * Standard teardown for every e2e test: closes all editors and deletes any
 * temp files created by openTempDocumentInEditor() during that test.
 */
export async function teardownTest(): Promise<void> {
    await closeAllEditors();
    deleteTempDocuments();
}

/**
 * Tracks whether the language server has been warmed up at least once during
 * this test run. Used by createSuiteSetup to skip the warm-up for subsequent
 * suites and avoid redundant ~30 s waits.
 */
let serverWarmedUp = false;

/**
 * Returns a suiteSetup callback that installs the language server and logs completion.
 * Also waits for the language server to be fully connected (server-side commands
 * registered) by opening a document that produces diagnostics before returning.
 * The warm-up is performed only once per test run; subsequent suites reuse the
 * already-running server and skip straight to the completion log.
 */
export function createSuiteSetup(suiteName: string): () => Promise<void> {
    return () => runSuiteSetup(suiteName);
}

function alwaysTrue(): boolean {
    return true;
}

async function activateExtension(): Promise<unknown> {
    const ext = vscode.extensions.getExtension("davelopez.galaxy-language-server");
    return ext?.isActive ? ext.exports : await ext?.activate();
}

function resolveAfterDelay(ms: number, resolve: () => void): void {
    setTimeout(resolve, ms);
}

function hasDiagnosticsForUri(docUri: vscode.Uri): boolean {
    return vscode.languages.getDiagnostics(docUri).length > 0;
}

function createHasDiagnosticsPredicate(docUri: vscode.Uri): () => boolean {
    return () => hasDiagnosticsForUri(docUri);
}

function insertTrailingSpaceAtPosition(position: vscode.Position, editBuilder: vscode.TextEditorEdit): void {
    editBuilder.insert(position, " ");
}

function createInsertTrailingSpaceCallback(position: vscode.Position): (editBuilder: vscode.TextEditorEdit) => void {
    return (editBuilder) => insertTrailingSpaceAtPosition(position, editBuilder);
}

class DiagnosticsWaiter {
    private timer?: ReturnType<typeof setTimeout>;
    private disposable?: vscode.Disposable;
    private resolve!: () => void;

    constructor(
        private readonly docUri: vscode.Uri,
        private readonly timeoutInMilliseconds: number,
        private readonly predicate: () => boolean
    ) { }

    public wait(): Promise<void> {
        return new Promise<void>((resolve) => {
            this.resolve = resolve;
            this.disposable = vscode.languages.onDidChangeDiagnostics(this.handleDiagnosticsChange);
            this.timer = setTimeout(this.handleTimeout, this.timeoutInMilliseconds);
        });
    }

    private isMatchingUri(event: vscode.DiagnosticChangeEvent): boolean {
        return event.uris.some((uri: vscode.Uri) => uri.toString() === this.docUri.toString());
    }

    private complete(): void {
        if (this.timer) {
            clearTimeout(this.timer);
        }
        this.disposable?.dispose();
        this.resolve();
    }

    private handleDiagnosticsChange = (event: vscode.DiagnosticChangeEvent): void => {
        if (!this.isMatchingUri(event)) {
            return;
        }
        if (!this.predicate()) {
            return;
        }
        this.complete();
    };

    private handleTimeout = (): void => {
        this.disposable?.dispose();
        this.resolve();
    };
}

async function runSuiteSetup(suiteName: string): Promise<void> {
    if (!serverWarmedUp) {
        const result = await ensureGalaxyLanguageServerInstalled();
        assert.ok(result);
        const { editor, document } = await openTempDocumentInEditor("<tool></tool>");
        await triggerValidationOnSave(editor, document.uri, 5000);
        await closeAllEditors();
        deleteTempDocuments();
        serverWarmedUp = true;
    }
    console.log(`[e2e] ${suiteName} test suite setup completed`);
}
