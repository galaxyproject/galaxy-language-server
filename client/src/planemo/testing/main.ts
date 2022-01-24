"use strict";

import * as vscode from "vscode";
import { TestTag } from "vscode";
import { LanguageClient } from "vscode-languageclient/node";
import { ITestsProvider, testDataMap, ToolTestSuite } from "../../testing/common";
import { LanguageServerTestProvider } from "../../testing/testsProvider";
import { IConfigurationFactory } from "../configuration";
import { PlanemoTestRunner } from "./testRunner";

const runnableTag = new TestTag("runnable");

export function setupTesting(
    client: LanguageClient,
    context: vscode.ExtensionContext,
    configFactory: IConfigurationFactory
) {
    const testProvider = new LanguageServerTestProvider(client);
    const planemoTestRunner = new PlanemoTestRunner();

    const controller = vscode.tests.createTestController("planemo-test-adapter", "Planemo Test Controller");
    context.subscriptions.push(controller);

    controller.resolveHandler = async (item) => {
        if (!configFactory.getConfiguration().planemo().testing().enabled()) return;

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
                testNode.children.forEach((node) => {
                    run.enqueued(node);
                });
                queue.push(testNode);
            }
        };

        const runTestQueue = async () => {
            for (const testNode of queue) {
                if (!cancellation.isCancellationRequested) {
                    await planemoTestRunner.run(configFactory.getConfiguration().planemo(), testNode, run);
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

    context.subscriptions.push(
        vscode.workspace.onDidOpenTextDocument(async (document) => {
            if (!configFactory.getConfiguration().planemo().testing().enabled()) return;
            await updateTestNodeFromDocument(testProvider, document, controller);
        }),
        vscode.workspace.onDidSaveTextDocument(async (document) => {
            if (!configFactory.getConfiguration().planemo().testing().autoTestDiscoverOnSaveEnabled()) return;
            await updateTestNodeFromDocument(testProvider, document, controller);
        })
    );
}

async function updateTestNodeFromDocument(
    testProvider: ITestsProvider,
    document: vscode.TextDocument,
    controller: vscode.TestController
) {
    const result = await testProvider.discoverTestsInDocument(document);
    if (result) {
        const suite = resolveTestSuite(controller, result);
        controller.items.add(suite);
    }
}

async function resolveAllTestsInWorkspace(testProvider: ITestsProvider, controller: vscode.TestController) {
    const result = await testProvider.discoverWorkspaceTests();
    const suites: vscode.TestItem[] = [];
    result.forEach((toolTestSuite) => {
        const suite = resolveTestSuite(controller, toolTestSuite);
        suites.push(suite);
    });
    controller.items.replace(suites);
}

function resolveTestSuite(controller: vscode.TestController, toolTestSuite: ToolTestSuite) {
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
    return suite;
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
