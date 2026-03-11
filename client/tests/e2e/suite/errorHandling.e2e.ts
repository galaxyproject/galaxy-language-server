import * as assert from "assert";
import * as vscode from "vscode";
import {
    createSuiteSetup,
    getErrorDiagnostics,
    openTempDocumentInEditor,
    saveAndWaitForDiagnostics,
    teardownTest,
    triggerValidationOnSave,
    assertHasErrors,
} from "./helpers";

suite("Error Handling Tests", () => {
    suiteSetup(createSuiteSetup("Error Handling"));
    teardown(teardownTest);

    test("Diagnostics are cleared when document becomes valid", async () => {
        const { editor, document } = await openTempDocumentInEditor("<tool></tool>");
        await triggerValidationOnSave(editor, document.uri, 10000);
        assertHasErrors(document.uri);

        // Fix the document by replacing it with a structurally complete valid tool.
        const validToolXml = [
            '<tool id="fixed" name="fixed" version="0.1.0">',
            '    <command detect_errors="exit_code"><![CDATA[echo hello]]></command>',
            '    <inputs/>',
            '    <outputs/>',
            '    <help><![CDATA[Help text.]]></help>',
            '</tool>',
        ].join("\n");
        const fullRange = new vscode.Range(
            new vscode.Position(0, 0),
            document.lineAt(document.lineCount - 1).range.end
        );
        await editor.edit((editBuilder) => editBuilder.replace(fullRange, validToolXml));

        const errorDiagnostics = await saveAndWaitForDiagnostics(document, vscode.DiagnosticSeverity.Error);

        assert.equal(
            errorDiagnostics.length,
            0,
            "Required attribute errors should be gone after adding valid id and name attributes"
        );
    });
});