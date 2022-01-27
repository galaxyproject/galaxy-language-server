"use strict";

import * as vscode from "vscode";
import { TestTag, window } from "vscode";
import { LanguageClient } from "vscode-languageclient/node";
import { Settings } from "../../configuration/workspaceConfiguration";
import { ITestsProvider, testDataMap, testSuiteByUriPath, ToolTestSuite } from "../../testing/common";
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
        if (!item) {
            await refreshAllTestsInWorkspace(testProvider, controller, configFactory);
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

        enqueueTests(request.include ?? gatherRunnableTestItems(controller.items)).then(runTestQueue);
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
        }),
        vscode.workspace.onDidCloseTextDocument(async (document) => {
            if (!configFactory.getConfiguration().planemo().testing().enabled()) return;
            await removeTestNodeFromDocument(document, controller);
        }),
        vscode.workspace.onDidChangeConfiguration(async (configurationChange) => {
            const sectionsToReload = [
                Settings.Planemo.ENV_PATH,
                Settings.Planemo.GALAXY_ROOT,
                Settings.Planemo.Testing.ENABLED,
            ];

            const needsReload = sectionsToReload.some((section) => configurationChange.affectsConfiguration(section));
            if (needsReload) {
                await refreshAllTestsInWorkspace(testProvider, controller, configFactory);
            }
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
        const suite = refreshTestsFromSuite(controller, result);
        if (suite) {
            controller.items.add(suite);
        }
    }
}

async function removeTestNodeFromDocument(document: vscode.TextDocument, controller: vscode.TestController) {
    const suite = testSuiteByUriPath.get(document.uri.fsPath);
    if (suite) {
        controller.items.delete(suite.id);
        testSuiteByUriPath.delete(document.uri.fsPath);
    }
}

async function refreshAllTestsInWorkspace(
    testProvider: ITestsProvider,
    controller: vscode.TestController,
    configFactory: IConfigurationFactory
) {
    clearAllTestItems(controller);
    const planemoConfig = configFactory.getConfiguration().planemo();
    if (!planemoConfig.testing().enabled()) return;

    const validationResult = await planemoConfig.validate();
    if (validationResult.hasErrors()) {
        window.showErrorMessage(validationResult.getErrorsAsString());
        return;
    }

    const result = await testProvider.discoverWorkspaceTests();
    const suites: vscode.TestItem[] = [];
    result.forEach((toolTestSuite) => {
        const suite = refreshTestsFromSuite(controller, toolTestSuite);
        if (suite) {
            suites.push(suite);
        }
    });
    controller.items.replace(suites);
}

function clearAllTestItems(controller: vscode.TestController) {
    testSuiteByUriPath.clear();
    const runnableTests = gatherRunnableTestItems(controller.items);
    runnableTests.forEach((test) => {
        controller.items.delete(test.id);
    });
}

function refreshTestsFromSuite(
    controller: vscode.TestController,
    toolTestSuite: ToolTestSuite
): vscode.TestItem | undefined {
    const suite = controller.createTestItem(toolTestSuite.id, toolTestSuite.label, toolTestSuite.uri);
    if (!suite.uri) return undefined;

    suite.range = toolTestSuite.range;
    suite.tags = [...suite.tags, runnableTag]; // Only suites are runnable for now
    toolTestSuite.children.forEach((toolTestCase) => {
        const testCase = controller.createTestItem(toolTestCase.id, toolTestCase.label, toolTestCase.uri);
        testCase.range = toolTestCase.range;
        testDataMap.set(testCase, toolTestCase);
        suite.children.add(testCase);
    });
    testDataMap.set(suite, toolTestSuite);
    testSuiteByUriPath.set(suite.uri.fsPath, suite);
    return suite;
}

function gatherRunnableTestItems(collection: vscode.TestItemCollection) {
    const runnableItems: vscode.TestItem[] = [];
    collection.forEach((item) => {
        const data = testDataMap.get(item);
        if (data instanceof ToolTestSuite) {
            runnableItems.push(item);
        }
    });
    return runnableItems;
}
