import { unlinkSync } from 'fs';
import * as path from 'path';
import * as tmp from 'tmp';
import { TestEvent, TestSuiteInfo } from 'vscode-test-adapter-api';
import { TOOL_DOCUMENT_EXTENSION } from '../../constants';
import { IProcessExecution, runProcess } from '../../processRunner';
import { ITestRunner } from '../../testing/testRunner';
import { IPlanemoConfiguration } from '../configuration';
import { parseTestStates } from './testsReportParser';


export class PlanemoTestRunner implements ITestRunner {

    private readonly testExecutions: Map<string, IProcessExecution> = new Map<string, IProcessExecution>();

    constructor(
        public readonly adapterId: string
    ) { }

    public async run(planemoConfig: IPlanemoConfiguration, testSuite: TestSuiteInfo): Promise<TestEvent[]> {
        if (!planemoConfig.enabled() || !planemoConfig.testing().enabled()) {
            return [];
        }

        const testSuiteId = testSuite.id;
        const testFile = testSuite.file ? testSuite.file : `${planemoConfig.getCwd()}/${testSuiteId}.${TOOL_DOCUMENT_EXTENSION}`;
        try {
            const { file: output_json_file, cleanupCallback } = await this.getJsonReportPath(testFile);

            const testRunArguments = [
                `test`,
                `--galaxy_root=${planemoConfig.galaxyRoot()}`,
                `--test_output_json=${output_json_file}`,
                testFile,
            ]

            const testExecution = this.runPlanemoTest(planemoConfig, testRunArguments);

            this.testExecutions.set(testSuiteId, testExecution);
            await testExecution.complete();

            const states = await parseTestStates(output_json_file, testSuite);

            cleanupCallback();

            return states
        }
        catch (err) {
            console.log(err)
            return []
        }
        finally {
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
    }

    public isRunning(): boolean {
        return this.testExecutions.size > 0;
    }

    private runPlanemoTest(planemoConfig: IPlanemoConfiguration, args: string[]): IProcessExecution {
        const planemoPath = planemoConfig.envPath();
        return runProcess(planemoPath, args, { cwd: planemoConfig.getCwd() });

    }

    private async getJsonReportPath(testFile: string | undefined): Promise<{ file: string, cleanupCallback: () => void }> {
        if (testFile !== undefined) {
            const baseDir = path.dirname(testFile);
            const testFileName = path.basename(testFile, TOOL_DOCUMENT_EXTENSION);
            const reportFile = path.resolve(baseDir, `${testFileName}json`);

            return Promise.resolve({
                file: reportFile,
                cleanupCallback: () => { unlinkSync(reportFile); },
            });
        }
        return await this.createTemporaryFile();
    }

    private async createTemporaryFile(): Promise<{ file: string, cleanupCallback: () => void }> {
        return new Promise<{ file: string, cleanupCallback: () => void }>((resolve, reject) => {
            tmp.file((error, file, _, cleanupCallback) => {
                if (error) {
                    reject(new Error(`Can not create temporary file ${file}: ${error}`));
                }
                resolve({ file, cleanupCallback });
            });
        });
    }
}
