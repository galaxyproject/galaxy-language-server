// You can import and use all API from the 'vscode' module
import * as vscode from "vscode";
import * as path from "path";
import {
    activateAndOpenInEditor,
    getDocUri,
    closeAllEditors,
    assertDiagnostics,
    ensureGalaxyLanguageServerInstalled,
    waitForDiagnostics,
} from "./helpers";
import * as assert from "assert";

suite("Extension Test Suite", () => {
    suiteSetup(async () => {
        const result = await ensureGalaxyLanguageServerInstalled();
        assert.ok(result);
        console.log("[e2e] Suite setup completed");
    });
    teardown(closeAllEditors);
    suite("Validation Tests", () => {
        test("Valid tool returns empty diagnostics", async () => {
            const docUri = getDocUri(path.join("test_tool_01.xml"));
            await activateAndOpenInEditor(docUri);

            await waitForDiagnostics(docUri);
            await assertDiagnostics(docUri, []);
        });

        test("Valid macro file returns empty diagnostics", async () => {
            const docUri = getDocUri(path.join("macros_01.xml"));
            await activateAndOpenInEditor(docUri);

            await waitForDiagnostics(docUri);
            await assertDiagnostics(docUri, []);
        });

        test("Invalid tool should return diagnostics for required attributes 'id' and 'name'", async () => {
            const docUri = getDocUri(path.join("test_invalid_tool_01.xml"));
            await activateAndOpenInEditor(docUri);

            await waitForDiagnostics(docUri);
            await assertDiagnostics(docUri, [
                {
                    message: "Element 'tool': The attribute 'id' is required but missing.",
                    range: new vscode.Range(new vscode.Position(0, 0), new vscode.Position(0, 0)),
                    severity: vscode.DiagnosticSeverity.Error,
                },
                {
                    message: "Element 'tool': The attribute 'name' is required but missing.",
                    range: new vscode.Range(new vscode.Position(0, 0), new vscode.Position(0, 0)),
                    severity: vscode.DiagnosticSeverity.Error,
                },
            ]);
        });

        test("Invalid tool document with syntax error should return diagnostic", async () => {
            const docUri = getDocUri(path.join("test_syntax_error_01.xml"));
            await activateAndOpenInEditor(docUri);

            await waitForDiagnostics(docUri);
            await assertDiagnostics(docUri, [
                {
                    message: "Couldn't find end of Start Tag tool line 1, line 2, column 1",
                    range: new vscode.Range(new vscode.Position(1, 0), new vscode.Position(1, 1)),
                    severity: vscode.DiagnosticSeverity.Error,
                },
            ]);
        });

        test("Invalid macro document with syntax error should return diagnostic", async () => {
            const docUri = getDocUri(path.join("test_syntax_error_macro_01.xml"));
            await activateAndOpenInEditor(docUri);

            await waitForDiagnostics(docUri);
            await assertDiagnostics(docUri, [
                {
                    message: "Premature end of data in tag macros line 1, line 2, column 1",
                    range: new vscode.Range(new vscode.Position(1, 0), new vscode.Position(1, 1)),
                    severity: vscode.DiagnosticSeverity.Error,
                },
            ]);
        });
    });
});
