import { unlinkSync } from "fs";
import * as path from "path";
import * as tmp from "tmp";
import { TestItem, TestMessage, TestRun } from "vscode";
import { Constants } from "../../constants";
import { IProcessExecution, runProcess } from "../../processRunner";
import { CRLF } from "../../testing/common";
import { ITestRunner } from "../../testing/testRunner";
import { OutputHighlight } from "../../utils";
import { IPlanemoConfiguration } from "../configuration";
import { parseTestStates } from "./testsReportParser";
import { logger } from "../../logger";

export class PlanemoTestRunner implements ITestRunner {
    private readonly testExecutions: Map<string, IProcessExecution> = new Map<string, IProcessExecution>();

    public async run(planemoConfig: IPlanemoConfiguration, testNode: TestItem, runInstance: TestRun): Promise<void> {
        logger.info(`Starting test run for ${testNode.id}`);
        runInstance.appendOutput(`Running ${OutputHighlight.green(testNode.id)} tool test suite${CRLF}`);

        const testSuiteId = testNode.id;
        const testFileUri = testNode.uri;

        if (testFileUri === undefined) {
            logger.error(`Test file URI not found for ${testSuiteId}`);
            runInstance.errored(testNode, new TestMessage("Target tool XML file not found."));
            testNode.children.forEach((node) => runInstance.skipped(node));
            return;
        }

        testNode.children.forEach((node) => runInstance.started(node));

        const testFile = testFileUri.fsPath;
        try {
            const { file: output_json_file, cleanupCallback } = await this.getJsonReportPath(testFile);
            const htmlReportFile = this.getTestHtmlReportFilePath(testFile);

            const testRunArguments = this.buildTestArguments(planemoConfig, output_json_file, htmlReportFile, testFile);

            logger.debug(`Planemo test command: planemo ${testRunArguments.join(" ")}`);
            runInstance.appendOutput(
                `with:${CRLF}${CRLF}${OutputHighlight.cyan("planemo " + testRunArguments.join(" "))}${CRLF}${CRLF}`
            );

            const testExecution = this.runPlanemoTest(planemoConfig, testRunArguments);

            this.testExecutions.set(testSuiteId, testExecution);
            const result = await testExecution.complete();

            logger.info(`Test execution completed for ${testSuiteId} with exit code ${result.exitCode}`);

            await parseTestStates(testNode, runInstance, output_json_file);

            cleanupCallback();

            runInstance.appendOutput(`Completed ${OutputHighlight.green(testNode.id)} tool testing${CRLF}${CRLF}`);
            runInstance.appendOutput(`See full test report: ${OutputHighlight.yellow(htmlReportFile)}${CRLF}`);
        } catch (err: any) {
            logger.error(`Test execution failed for ${testSuiteId}: ${err}`);
            runInstance.errored(testNode, new TestMessage(`Unexpected error when running tests:\n${err}`));
        } finally {
            this.testExecutions.delete(testSuiteId);
        }
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
        testFile: string
    ) {
        const extraParams = this.getTestExtraParams(planemoConfig);
        const baseArguments = [
            `test`,
            `--galaxy_root`,
            `${planemoConfig.galaxyRoot()}`,
            `--test_output_json`,
            `${output_json_file}`,
            `--test_output`,
            `${htmlReportFile}`,
        ];

        const testRunArguments = baseArguments.concat(extraParams).concat(`${testFile}`);
        return testRunArguments;
    }
}
