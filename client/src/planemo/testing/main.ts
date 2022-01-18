"use strict";

import * as vscode from "vscode";
import { testDataMap, ToolTestSuite } from "../../testing/common";
import { LanguageServerTestProvider } from "../../testing/testsProvider";
import { IConfigurationFactory } from "../configuration";
import { PlanemoTestRunner } from "./testRunner";

export function setupTesting(context: vscode.ExtensionContext, configFactory: IConfigurationFactory) {
    const testProvider = new LanguageServerTestProvider();
    const planemoTestRunner = new PlanemoTestRunner();

    const planemoConfig = configFactory.getConfiguration().planemo();

    if (!planemoConfig.testing().enabled()) return;

    const controller = vscode.tests.createTestController("planemo-test-adapter", "Planemo Test Controller");
    context.subscriptions.push(controller);

    controller.resolveHandler = async (item) => {
        if (!item) {
            const result = await testProvider.discoverWorkspaceTests();
            const suites: vscode.TestItem[] = [];
            result.forEach((toolTestSuite) => {
                const suite = controller.createTestItem(toolTestSuite.id, toolTestSuite.label, toolTestSuite.uri);
                suite.range = toolTestSuite.range;
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
        } else {
            // TODO resolve tests for a particular tool file
        }
    };

    const runHandler = (request: vscode.TestRunRequest, cancellation: vscode.CancellationToken) => {
        const queue: { test: vscode.TestItem; data: ToolTestSuite }[] = [];
        const run = controller.createTestRun(request);
        const discoverTests = async (tests: Iterable<vscode.TestItem>) => {
            for (const test of tests) {
                if (request.exclude?.includes(test)) {
                    continue;
                }

                const data = testDataMap.get(test);
                if (data instanceof ToolTestSuite) {
                    run.enqueued(test);
                    queue.push({ test, data });
                }
            }
        };

        const runTestQueue = async () => {
            for (const { test, data } of queue) {
                run.appendOutput(`Running ${test.id}\r\n`);
                if (cancellation.isCancellationRequested) {
                    run.skipped(test);
                } else {
                    run.started(test);
                    await planemoTestRunner.run(planemoConfig, test, run);
                }
                run.appendOutput(`Completed ${test.id}\r\n`);
            }
            run.end();
        };

        discoverTests(request.include ?? gatherTestItems(controller.items)).then(runTestQueue);
    };

    controller.createRunProfile("Run Tests", vscode.TestRunProfileKind.Run, runHandler, true);
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
