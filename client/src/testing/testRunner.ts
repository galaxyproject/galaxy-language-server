import { TestEvent, TestSuiteInfo } from "vscode-test-adapter-api";
import { IPlanemoConfiguration } from "../planemo/configuration";

export interface ITestRunner {
    readonly adapterId: string;

    run(config: IPlanemoConfiguration, testSuite: TestSuiteInfo): Promise<TestEvent[]>;

    cancel(): void;

    isRunning(): boolean;
}
