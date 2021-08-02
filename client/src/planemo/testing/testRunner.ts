import { unlinkSync } from "fs";
import * as path from "path";
import * as tmp from "tmp";
import { OutputChannel, window } from "vscode";
import { TestEvent, TestSuiteInfo } from "vscode-test-adapter-api";
import { Constants } from "../../constants";
import { IProcessExecution, runProcess } from "../../processRunner";
import { ITestRunner } from "../../testing/testRunner";
import { IPlanemoConfiguration } from "../configuration";
import { parseTestStates } from "./testsReportParser";

export class PlanemoTestRunner implements ITestRunner {
    private readonly testExecutions: Map<string, IProcessExecution> = new Map<string, IProcessExecution>();
    private _channel: OutputChannel = window.createOutputChannel(Constants.PLANEMO_TEST_OUTPUT_CHANNEL);

    constructor(public readonly adapterId: string) {}

    public async run(planemoConfig: IPlanemoConfiguration, testSuite: TestSuiteInfo): Promise<TestEvent[]> {
        if (!planemoConfig.enabled() || !planemoConfig.testing().enabled()) {
            return [];
        }

        const testSuiteId = testSuite.id;
        const testFile = testSuite.file
            ? testSuite.file
            : `${planemoConfig.getCwd()}/${testSuiteId}.${Constants.TOOL_DOCUMENT_EXTENSION}`;
        try {
            const { file: output_json_file, cleanupCallback } = await this.getJsonReportPath(testFile);
            const htmlReportFile = this.getTestHtmlReportFilePath(testFile);
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

            this._channel.appendLine(`Running planemo ${testRunArguments.join(" ")}`);

            const testExecution = this.runPlanemoTest(planemoConfig, testRunArguments);

            this.testExecutions.set(testSuiteId, testExecution);
            await testExecution.complete();

            const states = await parseTestStates(output_json_file, testSuite, htmlReportFile);

            cleanupCallback();

            this.showSummaryLog(states);

            return states;
        } catch (err) {
            this.showErrorLog(err);
            return [];
        } finally {
            this.testExecutions.delete(testSuiteId);
        }
    }

    public cancel(): void {
        this.testExecutions.forEach((execution, test) => {
            try {
                execution.cancel();
            } catch (error) {
                console.log(`Cancelling execution of ${test} failed: ${error}`);
            }
        });
        this._channel.appendLine("Tests run cancelled.");
    }

    public isRunning(): boolean {
        return this.testExecutions.size > 0;
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

    private showErrorLog(errorMessage: string) {
        this._channel.appendLine(errorMessage);
        this._channel.show();
    }

    private showSummaryLog(states: TestEvent[]) {
        let statesMap = new Map<string, number>();
        states.forEach((test) => {
            let stateCount = statesMap.get(test.state);
            stateCount = stateCount === undefined ? 1 : stateCount + 1;
            statesMap.set(test.state, stateCount);
        });
        this._channel.appendLine(`\n${states.length} tests completed:`);
        statesMap.forEach((count, state) => {
            this._channel.appendLine(`  ${count} ${state}`);
        });
        this._channel.append("\n");
    }
}
