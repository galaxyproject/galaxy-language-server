import { EOL } from "os";
import { TestEvent, TestInfo, TestSuiteInfo } from "vscode-test-adapter-api";
import { TestState } from "../../testing/common";
import { readFile } from "../../utils";

type PlanemoTestState = 'success' | 'failure' | 'skip' | 'error';

const stateMap: Map<PlanemoTestState, TestState> = new Map<PlanemoTestState, TestState>([
    ['success', 'passed'],
    ['failure', 'failed'],
    ['skip', 'skipped'],
    ['error', 'errored'],
])

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

export async function parseTestStates(outputJsonFile: string, testSuite: TestSuiteInfo): Promise<TestEvent[]> {
    const content = await readFile(outputJsonFile);
    const parseResult = await JSON.parse(content);
    return parseTestResults(parseResult, testSuite);
}

function parseTestResults(parserResult: any, testSuite: TestSuiteInfo): TestEvent[] {
    if (!parserResult) {
        return [];
    }
    const testSuiteResults: ITestSuiteResult = parserResult;

    const testResults: TestEvent[] = []
    testSuiteResults.tests.forEach(testCaseResult => {
        const testInfo = getTestInfo(testCaseResult, testSuite);
        const adatedResult = adaptTestResult(testCaseResult, testInfo);
        if (adatedResult !== undefined) {
            testResults.push(adatedResult);
        }
    });

    return testResults
}

function getTestInfo(result: ITestCaseResult, suite: TestSuiteInfo): TestInfo | undefined {
    try {
        const testInfo = suite.children[result.data.test_index] as TestInfo;
        return testInfo;
    }
    catch {
        return undefined;
    }
}

function adaptTestResult(testResult: ITestCaseResult, testInfo: TestInfo | undefined): TestEvent | undefined {
    if (!testResult.has_data) {
        return undefined;
    }
    const state = adapTestState(testResult);
    const testId = adaptTestId(testResult);
    const message = adaptTestMessage(testResult);
    const line = testInfo ? testInfo.line : 0;
    const result: TestEvent = {
        type: 'test',
        state: state,
        test: testId,
        message: message,
        decorations: getDecorations(state, line, message),
        description: adaptDescription(testResult),
    }
    return result;
}

function adapTestState(testResult: ITestCaseResult): TestState {
    const adapted = stateMap.get(testResult.data.status);
    if (adapted === undefined) return 'errored'
    return adapted
}

function adaptTestId(testResult: ITestCaseResult): string {
    const testIndex = testResult.data.test_index + 1;
    return `${testResult.data.tool_id}:${testIndex}`
}

function adaptTestMessage(testResult: ITestCaseResult): string {
    try {
        if (testResult.data.output_problems) {
            return testResult.data.output_problems.join(EOL);
        }
        return testResult.data.status;
    }
    catch (err) {
        return err;
    }
}

function adaptDescription(testResult: ITestCaseResult): string | undefined {
    const time = testResult.data.time_seconds.toPrecision(2);
    return time ? `(${time}s)` : undefined
}

function getDecorations(state: TestState, line: number | undefined, message: string): { line: number, message: string }[] {
    if (state === 'passed') {
        return [];
    }
    if (!line) {
        return [];
    }
    return [{
        line: line,
        message,
    }];
}
