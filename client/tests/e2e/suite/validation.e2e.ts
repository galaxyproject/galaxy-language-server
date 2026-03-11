import * as vscode from "vscode";
import {
    assertDiagnostics,
    assertDiagnosticMessageExists,
    assertHasNoErrors,
    createSuiteSetup,
    openFixtureAndWaitForDiagnostics,
    openFixtureAndWaitForDiagnosticsToSettle,
    openTempDocumentInEditor,
    teardownTest,
    triggerValidationOnSave,
} from "./helpers";

suite("Validation Tests", () => {
    suiteSetup(createSuiteSetup("Validation"));
    teardown(teardownTest);

    test("Valid tool returns no errors", async () => {
        const { document } = await openFixtureAndWaitForDiagnostics("test_tool_01.xml");
        assertHasNoErrors(document.uri);
    });

    test("Valid macro file returns empty diagnostics", async () => {
        const { document } = await openFixtureAndWaitForDiagnosticsToSettle("macros_01.xml");
        await assertDiagnostics(document.uri, []);
    });

    test("Invalid tool should return diagnostics for required attributes 'id' and 'name'", async () => {
        const { editor, document } = await openTempDocumentInEditor("<tool></tool>");
        await triggerValidationOnSave(editor, document.uri);

        assertDiagnosticMessageExists(
            document.uri,
            "Element 'tool': The attribute 'id' is required but missing."
        );
        assertDiagnosticMessageExists(
            document.uri,
            "Element 'tool': The attribute 'name' is required but missing."
        );
    });

    test("Invalid tool document with syntax error should return diagnostic", async () => {
        const { document } = await openFixtureAndWaitForDiagnostics("test_syntax_error_01.xml");
        await assertDiagnostics(document.uri, [
            {
                message: "Couldn't find end of Start Tag tool line 1, line 2, column 1",
                range: new vscode.Range(new vscode.Position(1, 0), new vscode.Position(1, 1)),
                severity: vscode.DiagnosticSeverity.Error,
            },
        ]);
    });

    test("Invalid macro document with syntax error should return diagnostic", async () => {
        const { document } = await openFixtureAndWaitForDiagnostics("test_syntax_error_macro_01.xml");
        await assertDiagnostics(document.uri, [
            {
                message: "Premature end of data in tag macros line 1, line 2, column 1",
                range: new vscode.Range(new vscode.Position(1, 0), new vscode.Position(1, 1)),
                severity: vscode.DiagnosticSeverity.Error,
            },
        ]);
    });

    test("Lint Valid tool returns no errors or warnings", async () => {
        const { document } = await openFixtureAndWaitForDiagnosticsToSettle("validation/tool_02.xml", 1500);
        await assertDiagnostics(document.uri, []);
    });

    test("Linting valid tool with warnings should return warning diagnostics", async () => {
        const { document } = await openFixtureAndWaitForDiagnostics("validation/tool_01.xml");
        await assertDiagnostics(document.uri, [
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
