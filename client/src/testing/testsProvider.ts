import { commands, Uri } from "vscode";
import { Commands } from "../commands";
import { cloneRange } from "../utils";
import { IToolTestSuite, ToolTestCase, ToolTestSuite } from "./common";

export interface ITestsProvider {
    discoverWorkspaceTests(): Promise<Array<ToolTestSuite>>;
}

export class LanguageServerTestProvider implements ITestsProvider {
    async discoverWorkspaceTests(): Promise<Array<ToolTestSuite>> {
        const response = (await commands.executeCommand(Commands.DISCOVER_TESTS.external)) as Array<IToolTestSuite>;
        if (!response) return [];

        const testSuites: Array<ToolTestSuite> = [];
        response.forEach((suite) => {
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
            testSuites.push(suiteData);
        });
        return testSuites;
    }
}
