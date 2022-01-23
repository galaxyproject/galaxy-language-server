import { TestItem, TestRun } from "vscode";
import { IPlanemoConfiguration } from "../planemo/configuration";

export interface ITestRunner {
    run(config: IPlanemoConfiguration, testNode: TestItem, runInstance: TestRun): Promise<void>;

    cancel(runInstance: TestRun): void;
}
