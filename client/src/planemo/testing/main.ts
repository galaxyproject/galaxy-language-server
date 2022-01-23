"use strict";

import * as vscode from "vscode";
import { TestTag } from "vscode";
import { testDataMap, ToolTestSuite } from "../../testing/common";
import { ITestsProvider, LanguageServerTestProvider } from "../../testing/testsProvider";
import { IConfigurationFactory } from "../configuration";
import { PlanemoTestRunner } from "./testRunner";

const runnableTag = new TestTag("runnable");

export function setupTesting(context: vscode.ExtensionContext, configFactory: IConfigurationFactory) {
    const testProvider = new LanguageServerTestProvider();
    const planemoTestRunner = new PlanemoTestRunner();

    const planemoConfig = configFactory.getConfiguration().planemo();

    if (!planemoConfig.testing().enabled()) return;

    const controller = vscode.tests.createTestController("planemo-test-adapter", "Planemo Test Controller");
    context.subscriptions.push(controller);

    controller.resolveHandler = async (item) => {
        if (!item) {
            await resolveAllTestsInWorkspace(testProvider, controller);
        } else {
            // TODO resolve tests for a particular tool file
        }
    };

    const runHandler = (request: vscode.TestRunRequest, cancellation: vscode.CancellationToken) => {
        const queue: Array<vscode.TestItem> = [];
        const run = controller.createTestRun(request);

        const enqueueTests = async (tests: Iterable<vscode.TestItem>) => {
            for (const testNode of tests) {
                if (request.exclude?.includes(testNode)) {
                    continue;
                }
                run.enqueued(testNode);
                queue.push(testNode);
            }
        };

        const runTestQueue = async () => {
            for (const testNode of queue) {
                if (!cancellation.isCancellationRequested) {
                    await planemoTestRunner.run(planemoConfig, testNode, run);
                }
            }
            run.end();
        };

        cancellation?.onCancellationRequested(() => {
            planemoTestRunner.cancel(run);
        });

        enqueueTests(request.include ?? gatherTestItems(controller.items)).then(runTestQueue);
    };

    controller.createRunProfile("Run Tests", vscode.TestRunProfileKind.Run, runHandler, true, runnableTag);
}

async function resolveAllTestsInWorkspace(testProvider: ITestsProvider, controller: vscode.TestController) {
    const result = await testProvider.discoverWorkspaceTests();
    const suites: vscode.TestItem[] = [];
    result.forEach((toolTestSuite) => {
        const suite = controller.createTestItem(toolTestSuite.id, toolTestSuite.label, toolTestSuite.uri);
        suite.range = toolTestSuite.range;
        suite.tags = [...suite.tags, runnableTag]; // Only suites are runnable for now
        toolTestSuite.children.forEach((toolTestCase) => {
            const testCase = controller.createTestItem(toolTestCase.id, toolTestCase.label, toolTestCase.uri);
            testCase.range = toolTestCase.range;
            testDataMap.set(testCase, toolTestCase);
            suite.children.add(testCase);
        });
        testDataMap.set(suite, toolTestSuite);
        suites.push(suite);
    });
    controller.items.replace(suites);
}

function gatherTestItems(collection: vscode.TestItemCollection) {
    const runnableItems: vscode.TestItem[] = [];
    collection.forEach((item) => {
        const data = testDataMap.get(item);
        if (data instanceof ToolTestSuite) {
            runnableItems.push(item);
        }
    });
    return runnableItems;
}
