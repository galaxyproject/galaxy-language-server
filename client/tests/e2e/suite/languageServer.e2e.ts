import * as vscode from "vscode";
import {
    assertHasErrors,
    createSuiteSetup,
    openFixtureAndWaitForDiagnostics,
    openFixtureInEditor,
    teardownTest,
    waitForDiagnostics,
} from "./helpers";

suite("Language Server Tests", () => {
    suiteSetup(createSuiteSetup("Language Server"));
    teardown(teardownTest);

    test("Language server connects and provides diagnostics on file open", async () => {
        const { document } = await openFixtureAndWaitForDiagnostics("test_invalid_tool_01.xml");

        // Verify diagnostics are present (language server is running and reporting errors)
        assertHasErrors(document.uri);
    });

    test("Diagnostics update when document content changes", async () => {
        const { editor, document } = await openFixtureInEditor("simple_params_01.xml");

        // Remove the first character of the XML opening tag to make it invalid
        const edit = new vscode.TextEdit(
            new vscode.Range(new vscode.Position(0, 0), new vscode.Position(0, 1)),
            ""
        );
        await editor.edit((editBuilder) => editBuilder.replace(edit.range, edit.newText));

        // Wait for the language server to process the now-invalid document
        await waitForDiagnostics(document.uri, 2000);

        // Breaking the XML structure should produce at least one error diagnostic
        assertHasErrors(document.uri);
    });
});
