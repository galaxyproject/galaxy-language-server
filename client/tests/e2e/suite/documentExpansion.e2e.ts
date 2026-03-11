import * as assert from "assert";
import * as vscode from "vscode";
import {
    createSuiteSetup,
    executeCommandAndExpectSuccess,
    openFixtureInEditor,
    sleep,
    teardownTest,
} from "./helpers";
import { Commands, GeneratedExpandedDocument } from "../../../src/commands";

suite("Document Expansion Tests", () => {
    suiteSetup(createSuiteSetup("Document Expansion"));
    teardown(teardownTest);

    test("Generate expanded document command executes without error", async () => {
        const { document } = await openFixtureInEditor("test_tool_01.xml");

        const result = await executeCommandAndExpectSuccess<GeneratedExpandedDocument>(
            Commands.GENERATE_EXPANDED_DOCUMENT.internal,
            document.uri
        );

        assert.ok(!result.error_message, `Expansion should succeed but got: ${result.error_message}`);
        assert.ok(result.content && result.content.length > 0, "Expanded document should have content");
    });

    test("Preview expanded document command shows macro expansion", async () => {
        await openFixtureInEditor("test_tool_01.xml");

        // Execute preview expanded document command
        await vscode.commands.executeCommand(Commands.PREVIEW_EXPANDED_DOCUMENT.internal);
        await sleep(500);

        // Verify the expanded document panel was opened (it uses the gls-expand URI scheme)
        const expandedEditorOpen = vscode.window.visibleTextEditors.some(
            (e) => e.document.uri.scheme === "gls-expand"
        );
        assert.ok(expandedEditorOpen, "Preview command should open the expanded document in a side panel");
    });

    test("Document expansion resolves macro tokens in macro-enabled tools", async () => {
        const { document } = await openFixtureInEditor("validation/tool_02.xml");

        const result = await executeCommandAndExpectSuccess<GeneratedExpandedDocument>(
            Commands.GENERATE_EXPANDED_DOCUMENT.internal,
            document.uri
        );

        assert.ok(!result.error_message, `Expansion should succeed but got: ${result.error_message}`);
        assert.ok(result.content && result.content.length > 0, "Expanded content should have content");
        assert.ok(!result.content.includes("@TOOL_VERSION@"), "Expanded content should resolve @TOOL_VERSION@ token");
        assert.ok(!result.content.includes("@GALAXY_VERSION@"), "Expanded content should resolve @GALAXY_VERSION@ token");
        assert.ok(
            result.content.includes('version="3.7+galaxy0"'),
            "Expanded content should contain resolved version string"
        );
    });
});
