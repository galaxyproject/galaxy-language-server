import { unlinkSync } from "fs";
import * as path from "path";
import * as tmp from "tmp";
import { TestItem, TestMessage, TestRun } from "vscode";
import { Constants } from "../../constants";
import { IProcessExecution, runProcess } from "../../processRunner";
import { CRLF, testDataMap, ToolTestCase, ToolTestSuite } from "../../testing/common";
import { ITestRunner } from "../../testing/testRunner";
import { OutputHighlight } from "../../utils";
import { IPlanemoConfiguration } from "../configuration";
import { parseTestStates } from "./testsReportParser";
import { logger } from "../../logger";

type TestRunTargetType = "suite" | "single-test" | "multi-test";

interface IResolvedRunTarget {
    executionId: string;
    requestedNodes: TestItem[];
    runTargetLabel: string;
    suiteNode: TestItem;
    testIndices: number[];
    targetNode: TestItem;
    type: TestRunTargetType;
}

export class PlanemoTestRunner implements ITestRunner {
    private readonly testExecutions: Map<string, IProcessExecution> = new Map<string, IProcessExecution>();

    public async run(
        planemoConfig: IPlanemoConfiguration,
        testNodes: TestItem | readonly TestItem[],
        runInstance: TestRun
    ): Promise<void> {
        const requestedNodes = Array.isArray(testNodes) ? [...testNodes] : [testNodes];
        const resolvedRunTarget = this.resolveRunTarget(requestedNodes);
        if (!resolvedRunTarget) {
            const fallbackNode = requestedNodes[0];
            logger.error(`Unknown test node type for ${fallbackNode?.id ?? "unknown test selection"}`);
            if (fallbackNode) {
                runInstance.errored(fallbackNode, new TestMessage("Unsupported test item type."));
            }
            return;
        }

        const { executionId, requestedNodes: resolvedNodes, runTargetLabel, suiteNode, targetNode, testIndices, type } =
            resolvedRunTarget;
        const testFileUri = suiteNode.uri;

        logger.info(`Starting test run for ${executionId}`);
        runInstance.appendOutput(`Running ${OutputHighlight.green(targetNode.id)} ${runTargetLabel}${CRLF}`);

        if (testFileUri === undefined) {
            logger.error(`Test file URI not found for ${executionId}`);
            runInstance.errored(targetNode, new TestMessage("Target tool XML file not found."));
            if (type === "suite") {
                suiteNode.children.forEach((node) => runInstance.skipped(node));
            }
            return;
        }

        if (type === "suite") {
            suiteNode.children.forEach((node) => runInstance.started(node));
        } else {
            resolvedNodes.forEach((node) => runInstance.started(node));
        }

        if (type !== "suite" && testIndices.length !== resolvedNodes.length) {
            logger.error(`Cannot compute test indices for ${executionId}`);
            resolvedNodes.forEach((node) =>
                runInstance.errored(node, new TestMessage("Cannot determine one or more selected test indices."))
            );
            return;
        }

        const testFile = testFileUri.fsPath;
        try {
            const { file: output_json_file, cleanupCallback } = await this.getJsonReportPath(testFile);
            const htmlReportFile = this.getTestHtmlReportFilePath(testFile);

            const testRunArguments = this.buildTestArguments(
                planemoConfig,
                output_json_file,
                htmlReportFile,
                testFile,
                testIndices
            );

            logger.debug(`Planemo test command: planemo ${testRunArguments.join(" ")}`);
            runInstance.appendOutput(
                `with:${CRLF}${CRLF}${OutputHighlight.cyan("planemo " + testRunArguments.join(" "))}${CRLF}${CRLF}`
            );

            const testExecution = this.runPlanemoTest(planemoConfig, testRunArguments);

            this.testExecutions.set(executionId, testExecution);
            const result = await testExecution.complete();

            logger.info(`Test execution completed for ${executionId} with exit code ${result.exitCode}`);

            await parseTestStates(suiteNode, runInstance, output_json_file);

            cleanupCallback();

            runInstance.appendOutput(`Completed ${OutputHighlight.green(targetNode.id)} tool testing${CRLF}${CRLF}`);
            runInstance.appendOutput(`See full test report: ${OutputHighlight.yellow(htmlReportFile)}${CRLF}`);
        } catch (err: any) {
            logger.error(`Test execution failed for ${executionId}: ${err}`);
            resolvedNodes.forEach((node) =>
                runInstance.errored(node, new TestMessage(`Unexpected error when running tests:\n${err}`))
            );
        } finally {
            this.testExecutions.delete(executionId);
        }
    }

    private resolveRunTarget(testNodes: readonly TestItem[]): IResolvedRunTarget | undefined {
        if (testNodes.length === 0) {
            return undefined;
        }

        const firstNode = testNodes[0];
        const firstNodeType = this.getTestRunTargetType(firstNode);
        if (!firstNodeType) {
            return undefined;
        }

        if (firstNodeType === "suite") {
            return {
                executionId: firstNode.id,
                requestedNodes: [firstNode],
                runTargetLabel: "tool test suite",
                suiteNode: firstNode,
                targetNode: firstNode,
                testIndices: [],
                type: "suite",
            };
        }

        const suiteNode = firstNode.parent;
        if (!suiteNode) {
            logger.error(`Missing parent test suite for ${firstNode.id}`);
            return undefined;
        }

        const selectedTestNodes: TestItem[] = [];
        for (const testNode of testNodes) {
            const runTargetType = this.getTestRunTargetType(testNode);
            if (runTargetType !== "single-test" || testNode.parent?.id !== suiteNode.id) {
                logger.warn(`Skipping incompatible test selection ${testNode.id} for grouped execution in ${suiteNode.id}`);
                continue;
            }
            if (!selectedTestNodes.includes(testNode)) {
                selectedTestNodes.push(testNode);
            }
        }

        if (selectedTestNodes.length === 0) {
            return undefined;
        }

        const testIndices = this.getPlanemoTestIndices(selectedTestNodes);
        const type = selectedTestNodes.length === 1 ? "single-test" : "multi-test";
        const runTargetLabel =
            type === "single-test" ? "tool test case" : `${selectedTestNodes.length} selected tool tests`;
        const executionSuffix = testIndices.length > 0 ? testIndices.join(",") : selectedTestNodes.map((node) => node.id).join(",");

        return {
            executionId: `${suiteNode.id}:${executionSuffix}`,
            requestedNodes: selectedTestNodes,
            runTargetLabel,
            suiteNode,
            targetNode: selectedTestNodes[0],
            testIndices,
            type,
        };
    }

    private getTestRunTargetType(testNode: TestItem): TestRunTargetType | undefined {
        const testData = testDataMap.get(testNode);
        if (testData instanceof ToolTestSuite) {
            return "suite";
        }
        if (testData instanceof ToolTestCase) {
            return "single-test";
        }
        return undefined;
    }

    public cancel(runInstance: TestRun): void {
        logger.info(`Cancelling ${this.testExecutions.size} test execution(s)`);
        this.testExecutions.forEach((execution, test) => {
            try {
                runInstance.appendOutput(`${CRLF}Cancelling test run for ${OutputHighlight.green(test)} tool${CRLF}`);
                execution.cancel();
                logger.debug(`Cancelled test execution for ${test}`);
            } catch (error) {
                logger.error(`Failed to cancel test execution for ${test}: ${error}`);
                runInstance.appendOutput(
                    `${CRLF}Cancelling execution of ${OutputHighlight.green(test)} tests failed: ${error}${CRLF}`
                );
            }
        });
    }

    private runPlanemoTest(planemoConfig: IPlanemoConfiguration, args: string[]): IProcessExecution {
        const planemoPath = planemoConfig.binaryPath();
        return runProcess(planemoPath, args, { cwd: planemoConfig.getCwd() });
    }

    private async getJsonReportPath(
        testFile: string | undefined
    ): Promise<{ file: string; cleanupCallback: () => void }> {
        if (testFile !== undefined) {
            const baseDir = path.dirname(testFile);
            const testFileName = path.basename(testFile, Constants.TOOL_DOCUMENT_EXTENSION);
            const reportFile = path.resolve(baseDir, `${testFileName}json`);

            return Promise.resolve({
                file: reportFile,
                cleanupCallback: () => {
                    unlinkSync(reportFile);
                },
            });
        }
        return await this.createTemporaryFile();
    }

    private async createTemporaryFile(): Promise<{ file: string; cleanupCallback: () => void }> {
        return new Promise<{ file: string; cleanupCallback: () => void }>((resolve, reject) => {
            tmp.file((error, file, _, cleanupCallback) => {
                if (error) {
                    reject(new Error(`Can not create temporary file ${file}: ${error}`));
                }
                resolve({ file, cleanupCallback });
            });
        });
    }

    private getTestHtmlReportFilePath(testFile: string): string {
        const baseDir = path.dirname(testFile);
        const testFileName = path.basename(testFile, Constants.TOOL_DOCUMENT_EXTENSION).replace(".", "");
        const reportFile = path.resolve(baseDir, `${testFileName}_test_report.html`);
        return reportFile;
    }

    private getTestExtraParams(planemoConfig: IPlanemoConfiguration): string[] {
        const extraParams = planemoConfig.testing().extraParams();
        if (extraParams != "") {
            return extraParams.split(" ");
        }
        return [];
    }

    private buildTestArguments(
        planemoConfig: IPlanemoConfiguration,
        output_json_file: string,
        htmlReportFile: string,
        testFile: string,
        testIndices: number[] = []
    ) {
        const extraParams = this.getTestExtraParams(planemoConfig);
        const testIndexArguments = testIndices.flatMap((index) => ["--test_index", `${index + 1}`]);
        const baseArguments = [
            `test`,
            `--galaxy_root`,
            `${planemoConfig.galaxyRoot()}`,
            `--test_output_json`,
            `${output_json_file}`,
            `--test_output`,
            `${htmlReportFile}`,
        ];

        const testRunArguments = baseArguments.concat(testIndexArguments).concat(extraParams).concat(`${testFile}`);
        return testRunArguments;
    }

    private getPlanemoTestIndices(testNodes: readonly TestItem[]): number[] {
        const testIndices: number[] = [];

        for (const testNode of testNodes) {
            const testIndex = this.getPlanemoTestIndex(testNode.id);
            if (testIndex === undefined) {
                return [];
            }
            testIndices.push(testIndex);
        }

        return testIndices;
    }

    private getPlanemoTestIndex(testId: string): number | undefined {
        const testIdParts = testId.split(":");
        if (testIdParts.length < 2) {
            logger.warn(`Unexpected test id format for index parsing: ${testId}`);
            return undefined;
        }

        const testNumberToken = testIdParts[testIdParts.length - 1];
        const testCaseNumber = Number.parseInt(testNumberToken, 10);
        if (Number.isNaN(testCaseNumber) || testCaseNumber < 1) {
            logger.warn(`Unable to parse test index from id: ${testId} (token: ${testNumberToken})`);
            return undefined;
        }
        return testCaseNumber - 1;
    }
}
