import { LanguageClient, RequestType0 } from "vscode-languageclient/node";
import { TestSuiteInfo, TestInfo } from "vscode-test-adapter-api";
import { Commands } from "../commands";

export interface ITestsProvider {
    discoverTests(): Promise<TestSuiteInfo | undefined>;
}

namespace DiscoverTestRequest {
    export const type: RequestType0<TestSuiteInfo[], any> = new RequestType0(Commands.DISCOVER_TESTS);
}

export class LanguageServerTestProvider implements ITestsProvider {
    constructor(private readonly client: LanguageClient) {}

    async discoverTests(): Promise<TestSuiteInfo | undefined> {
        return await this.requestDiscoverTests();
    }

    private async requestDiscoverTests(): Promise<TestSuiteInfo | undefined> {
        let response = (await this.client.sendRequest(DiscoverTestRequest.type)) as TestSuiteInfo[];
        if (!response) return;

        const testSuites: TestSuiteInfo[] = [];
        response.forEach((suite) => {
            const tests: TestInfo[] = [];
            suite.children.forEach((test) => {
                const testInfo: TestInfo = {
                    type: "test",
                    id: test.id,
                    label: test.label,
                    file: test.file,
                    line: test.line,
                    description: test.description,
                    tooltip: test.tooltip,
                    debuggable: test.debuggable,
                    errored: test.errored,
                    message: test.message,
                };
                tests.push(testInfo);
            });
            const suiteInfo: TestSuiteInfo = {
                type: "suite",
                id: suite.id,
                label: suite.label,
                file: suite.file,
                line: suite.line,
                description: suite.description,
                tooltip: suite.tooltip,
                debuggable: suite.debuggable,
                errored: suite.errored,
                message: suite.message,
                children: tests,
            };
            testSuites.push(suiteInfo);
        });

        const result: TestSuiteInfo = {
            type: "suite",
            id: "root",
            label: "planemo",
            children: testSuites,
        };
        return result;
    }
}
