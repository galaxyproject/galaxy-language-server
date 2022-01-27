import { commands, TextDocument, Uri } from "vscode";
import { LanguageClient } from "vscode-languageclient/node";
import { Commands } from "../commands";
import { cloneRange } from "../utils";
import { ITestsProvider, IToolTestSuite, ToolTestCase, ToolTestSuite } from "./common";

export class LanguageServerTestProvider implements ITestsProvider {
    constructor(private readonly client: LanguageClient) {}

    async discoverWorkspaceTests(): Promise<Array<ToolTestSuite>> {
        const response = (await commands.executeCommand(
            Commands.DISCOVER_TESTS_IN_WORKSPACE.external
        )) as Array<IToolTestSuite>;
        if (!response) return [];

        const testSuites: Array<ToolTestSuite> = [];
        response.forEach((suite) => {
            const suiteData = this.buildSuiteData(suite);
            testSuites.push(suiteData);
        });
        return testSuites;
    }

    async discoverTestsInDocument(document: TextDocument): Promise<ToolTestSuite | undefined> {
        const param = this.client.code2ProtocolConverter.asTextDocumentIdentifier(document);
        const response = (await commands.executeCommand(
            Commands.DISCOVER_TESTS_IN_DOCUMENT.external,
            param
        )) as IToolTestSuite;
        if (!response) return undefined;

        const suiteData = this.buildSuiteData(response);
        return suiteData;
    }

    private buildSuiteData(suite: IToolTestSuite) {
        const testCases = suite.children.map(
            (test) => new ToolTestCase(test.id, test.label, Uri.parse(test.uri), cloneRange(test.range))
        );
        const suiteData = new ToolTestSuite(
            suite.id,
            suite.label,
            Uri.parse(suite.uri),
            cloneRange(suite.range),
            testCases
        );
        return suiteData;
    }
}
