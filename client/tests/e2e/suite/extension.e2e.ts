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

        test("Linting valid tool with warnings should return warning diagnostics", async () => {
            const docUri = getDocUri(path.join("validation/tool_01.xml"));
            await activateAndOpenInEditor(docUri);

            await waitForDiagnostics(docUri);
            await assertDiagnostics(docUri, [
                {
                    message: "Best practice violation [macros] elements should come before [command]",
                    range: new vscode.Range(new vscode.Position(5, 5), new vscode.Position(5, 11)),
                    severity: vscode.DiagnosticSeverity.Warning,
                },
                {
                    message: "Best practice violation [description] elements should come before [macros]",
                    range: new vscode.Range(new vscode.Position(9, 5), new vscode.Position(9, 16)),
                    severity: vscode.DiagnosticSeverity.Warning,
                },
                {
                    message: "No tests found, most tools should define test cases.",
                    range: new vscode.Range(new vscode.Position(0, 1), new vscode.Position(0, 5)),
                    severity: vscode.DiagnosticSeverity.Warning,
                },
                {
                    message: "Tool contains no outputs section, most tools should produce outputs.",
                    range: new vscode.Range(new vscode.Position(0, 1), new vscode.Position(0, 5)),
                    severity: vscode.DiagnosticSeverity.Warning,
                },
                {
                    message: "Found no input parameters.",
                    range: new vscode.Range(new vscode.Position(0, 1), new vscode.Position(0, 5)),
                    severity: vscode.DiagnosticSeverity.Warning,
                },
                {
                    message: "No help section found, consider adding a help section to your tool.",
                    range: new vscode.Range(new vscode.Position(0, 1), new vscode.Position(0, 5)),
                    severity: vscode.DiagnosticSeverity.Warning,
                },
                {
                    message: "Tool version [@TOOL_VERSION@+galaxy@VERSION_SUFFIX@] is not compliant with PEP 440.",
                    range: new vscode.Range(new vscode.Position(0, 1), new vscode.Position(0, 5)),
                    severity: vscode.DiagnosticSeverity.Warning,
                },
                {
                    message: "Command template contains TODO text.",
                    range: new vscode.Range(new vscode.Position(1, 5), new vscode.Position(1, 12)),
                    severity: vscode.DiagnosticSeverity.Warning,
                },
                {
                    message: "No citations found, consider adding citations to your tool.",
                    range: new vscode.Range(new vscode.Position(0, 1), new vscode.Position(0, 5)),
                    severity: vscode.DiagnosticSeverity.Warning,
                },
            ]);
        });
    });
});
