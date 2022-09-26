// You can import and use all API from the 'vscode' module
import * as vscode from "vscode";
import * as path from "path";
import { activateAndOpenInEditor, getDocUri, closeAllEditors, sleep, assertDiagnostics, setupServer } from "./helpers";
import * as assert from "assert";

suite("Extension Test Suite", () => {
    suiteSetup(async () => {
        const result = await setupServer();
        assert.ok(result);
    });
    teardown(closeAllEditors);
    suite("Validation Tests", () => {
        test("Tool should have minimum required attributes 'id' and 'name'", async () => {
            const docUri = getDocUri(path.join("test_invalid_tool_01.xml"));
            await activateAndOpenInEditor(docUri);

            await sleep(2000); // Wait for diagnostics
            await assertDiagnostics(docUri, [
                {
                    message: "Element 'tool': The attribute 'id' is required but missing.",
                    range: new vscode.Range(new vscode.Position(0, 0), new vscode.Position(0, 0)),
                    severity: 0,
                },
                {
                    message: "Element 'tool': The attribute 'name' is required but missing.",
                    range: new vscode.Range(new vscode.Position(0, 0), new vscode.Position(0, 0)),
                    severity: 0,
                },
            ]);
        });
    });
});
