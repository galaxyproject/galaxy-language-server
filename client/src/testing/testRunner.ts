import { TestItem, TestRun } from "vscode";
import { IPlanemoConfiguration } from "../planemo/configuration";

export interface ITestRunner {
    run(config: IPlanemoConfiguration, item: TestItem, options: TestRun): Promise<void>;

    cancel(): void;

    isRunning(): boolean;
}
