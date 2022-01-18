import { EOL } from "os";
import { TestItem, TestMessage, TestRun } from "vscode";
import { TestState } from "../../testing/common";
import { readFile } from "../../utils";

type PlanemoTestState = "success" | "failure" | "skip" | "error";

const stateMap: Map<PlanemoTestState, TestState> = new Map<PlanemoTestState, TestState>([
    ["success", "passed"],
    ["failure", "failed"],
    ["skip", "skipped"],
    ["error", "errored"],
]);

interface ITestSuiteResult {
    tests: ITestCaseResult[];
    version: string;
}

interface ITestCaseResult {
    id: string;
    has_data: boolean;
    data: ITestCaseData;
}

interface ITestCaseData {
    tool_id: string;
    tool_version: string;
    test_index: number;
    time_seconds: number;
    status: PlanemoTestState;
    job?: ITestCaseJobInfo;
    output_problems?: string[];
}

interface ITestCaseJobInfo {
    exit_code: number;
    galaxy_version: string;
    job_stderr: string;
    job_stdout: string;
    state: string;
    stderr: string;
    stdout: string;
    tool_id: string;
    tool_stderr: string;
    tool_stdout: string;
}

export async function parseTestStates(suite: TestItem, options: TestRun, outputJsonFile: string): Promise<void> {
    const content = await readFile(outputJsonFile);
    const parseResult = await JSON.parse(content);
    if (!parseResult) {
        options.errored(suite, new TestMessage(`Cannot read planemo test output from ${outputJsonFile}`));
        return;
    }
    const testSuiteResults: ITestSuiteResult = parseResult;
    testSuiteResults.tests.forEach((testCaseResult) => {
        const testCase = getTestCase(testCaseResult, suite);
        adaptTestResult(testCaseResult, testCase, options);
    });
}

function getTestCase(result: ITestCaseResult, suite: TestItem): TestItem | undefined {
    try {
        const testId = adaptTestId(result);
        const testCase = suite.children.get(testId) as TestItem;
        return testCase;
    } catch {
        return undefined;
    }
}

function adaptTestResult(testResult: ITestCaseResult, item: TestItem | undefined, options: TestRun) {
    if (!testResult.has_data || !item) {
        return undefined;
    }
    const state = adaptTestState(testResult);
    const message = new TestMessage(adaptTestMessage(testResult));
    const duration = testResult.data.time_seconds;

    switch (state) {
        case "passed":
            options.passed(item, duration);
            break;
        case "failed":
            options.failed(item, message, duration);
            break;
        default:
            options.errored(item, message, duration);
    }
}

function adaptTestState(testResult: ITestCaseResult): TestState {
    const adapted = stateMap.get(testResult.data.status);
    if (adapted === undefined) return "errored";
    return adapted;
}

function adaptTestId(testResult: ITestCaseResult): string {
    const testIndex = testResult.data.test_index + 1;
    return `${testResult.data.tool_id}:${testIndex}`;
}

function adaptTestMessage(testResult: ITestCaseResult): string {
    try {
        if (testResult.data.output_problems) {
            return testResult.data.output_problems.join(EOL);
        }
        return testResult.data.status;
    } catch (err: any) {
        return err;
    }
}
