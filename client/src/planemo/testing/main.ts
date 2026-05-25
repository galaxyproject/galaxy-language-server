"use strict";

import * as vscode from "vscode";
import { TestTag, window } from "vscode";
import { LanguageClient } from "vscode-languageclient/node";
import { Settings } from "../../configuration/workspaceConfiguration";
import { ITestsProvider, testDataMap, testSuiteByUriPath, ToolTestCase, ToolTestSuite } from "../../testing/common";
import { LanguageServerTestProvider } from "../../testing/testsProvider";
import { isGalaxyToolDocument } from "../../utils";
import { IConfigurationFactory } from "../configuration";
import { PlanemoTestRunner } from "./testRunner";
import { logger } from "../../logger";

const runnableTag = new TestTag("runnable");

interface IQueuedTestRun {
    requestedNodes: vscode.TestItem[];
    suiteNode: vscode.TestItem;
}

export function setupTesting(
    client: LanguageClient,
    context: vscode.ExtensionContext,
    configFactory: IConfigurationFactory
) {
    const testProvider = new LanguageServerTestProvider(client);
    const planemoTestRunner = new PlanemoTestRunner();
    const individualTestSupport = createIndividualTestSupportResolver(configFactory);

    const controller = vscode.tests.createTestController("planemo-test-adapter", "Galaxy Tools - Planemo Tests");
    context.subscriptions.push(controller);

    controller.resolveHandler = async (item) => {
        if (!item) {
            const supportsIndividualTestRun = await individualTestSupport.get();
            await refreshAllTestsInWorkspace(testProvider, controller, configFactory, supportsIndividualTestRun);
        } else {
            // TODO resolve tests for a particular tool file
        }
    };

    const runHandler = (request: vscode.TestRunRequest, cancellation: vscode.CancellationToken) => {
        const queue: IQueuedTestRun[] = [];
        const run = controller.createTestRun(request);
        const excludedNodes = new Set(request.exclude ?? []);

        const enqueueTests = async (tests: Iterable<vscode.TestItem>) => {
            const groupedTests = createQueuedTestRuns(tests, excludedNodes);
            for (const testRun of groupedTests) {
                if (testRun.requestedNodes.length === 0) {
                    continue;
                }
                if (testRun.requestedNodes.length === 1 && testRun.requestedNodes[0] === testRun.suiteNode) {
                    run.enqueued(testRun.suiteNode);
                    testRun.suiteNode.children.forEach((node) => {
                        if (!excludedNodes.has(node)) {
                            run.enqueued(node);
                        }
                    });
                } else {
                    testRun.requestedNodes.forEach((node) => run.enqueued(node));
                }
                queue.push(testRun);
            }
        };

        const runTestQueue = async () => {
            for (const testRun of queue) {
                if (!cancellation.isCancellationRequested) {
                    await planemoTestRunner.run(configFactory.getConfiguration().planemo(), testRun.requestedNodes, run);
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
            const supportsIndividualTestRun = await individualTestSupport.get();
            await updateTestNodeFromDocument(testProvider, document, controller, supportsIndividualTestRun);
        }),
        vscode.workspace.onDidSaveTextDocument(async (document) => {
            if (!configFactory.getConfiguration().planemo().testing().autoTestDiscoverOnSaveEnabled()) return;
            const supportsIndividualTestRun = await individualTestSupport.get();
            await updateTestNodeFromDocument(testProvider, document, controller, supportsIndividualTestRun);
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
                individualTestSupport.invalidate();
                const supportsIndividualTestRun = await individualTestSupport.get();
                await refreshAllTestsInWorkspace(testProvider, controller, configFactory, supportsIndividualTestRun);
            }
        })
    );
}

interface IIndividualTestSupportResolver {
    get(): Promise<boolean>;
    invalidate(): void;
}

function createIndividualTestSupportResolver(configFactory: IConfigurationFactory): IIndividualTestSupportResolver {
    let cachedBinaryPath: string | undefined;
    let cachedSupport: Promise<boolean> | undefined;

    return {
        async get(): Promise<boolean> {
            const planemoConfig = configFactory.getConfiguration().planemo();
            const binaryPath = planemoConfig.binaryPath();

            if (cachedSupport && cachedBinaryPath === binaryPath) {
                return cachedSupport;
            }

            cachedBinaryPath = binaryPath;
            cachedSupport = getIndividualTestRunSupport(configFactory);
            return cachedSupport;
        },
        invalidate(): void {
            cachedBinaryPath = undefined;
            cachedSupport = undefined;
        },
    };
}

async function getIndividualTestRunSupport(configFactory: IConfigurationFactory): Promise<boolean> {
    try {
        const planemoConfig = configFactory.getConfiguration().planemo();
        return await planemoConfig.testing().supportsIndividualTestRun(planemoConfig.binaryPath());
    } catch (error) {
        logger.warn(`Could not determine Planemo single-test support: ${error}`);
        return false;
    }
}

async function updateTestNodeFromDocument(
    testProvider: ITestsProvider,
    document: vscode.TextDocument,
    controller: vscode.TestController,
    supportsIndividualTestRun: boolean
) {
    if (!isGalaxyToolDocument(document)) {
        return;
    }
    const result = await testProvider.discoverTestsInDocument(document);
    if (result) {
        const suite = refreshTestsFromSuite(controller, result, supportsIndividualTestRun);
        if (suite) {
            controller.items.add(suite);
        }
    }
}

async function removeTestNodeFromDocument(document: vscode.TextDocument, controller: vscode.TestController) {
    if (!isGalaxyToolDocument(document)) {
        return;
    }
    const suite = testSuiteByUriPath.get(document.uri.fsPath);
    if (suite) {
        controller.items.delete(suite.id);
        testSuiteByUriPath.delete(document.uri.fsPath);
    }
}

async function refreshAllTestsInWorkspace(
    testProvider: ITestsProvider,
    controller: vscode.TestController,
    configFactory: IConfigurationFactory,
    supportsIndividualTestRun: boolean
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
        const suite = refreshTestsFromSuite(controller, toolTestSuite, supportsIndividualTestRun);
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
    toolTestSuite: ToolTestSuite,
    supportsIndividualTestRun: boolean
): vscode.TestItem | undefined {
    const suite = controller.createTestItem(toolTestSuite.id, toolTestSuite.label, toolTestSuite.uri);
    if (!suite.uri) return undefined;

    suite.range = toolTestSuite.range;
    // Suite runs are always supported; child tests are tagged conditionally below.
    suite.tags = [...suite.tags, runnableTag];
    toolTestSuite.children.forEach((toolTestCase) => {
        const testCase = controller.createTestItem(toolTestCase.id, toolTestCase.label, toolTestCase.uri);
        testCase.range = toolTestCase.range;
        if (supportsIndividualTestRun) {
            testCase.tags = [...testCase.tags, runnableTag];
        }
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

function createQueuedTestRuns(
    requestedTests: Iterable<vscode.TestItem>,
    excludedNodes: ReadonlySet<vscode.TestItem>
): IQueuedTestRun[] {
    const queuedRuns = new Map<string, IQueuedTestRun>();

    for (const testNode of requestedTests) {
        if (excludedNodes.has(testNode)) {
            continue;
        }

        const testData = testDataMap.get(testNode);
        if (testData instanceof ToolTestSuite) {
            const includedChildren: vscode.TestItem[] = [];
            testNode.children.forEach((childNode) => {
                if (!excludedNodes.has(childNode)) {
                    includedChildren.push(childNode);
                }
            });

            queuedRuns.set(testNode.id, {
                requestedNodes: includedChildren.length === testNode.children.size ? [testNode] : includedChildren,
                suiteNode: testNode,
            });
            continue;
        }

        if (!(testData instanceof ToolTestCase) || !testNode.parent) {
            continue;
        }

        const suiteRun = queuedRuns.get(testNode.parent.id);
        if (suiteRun && suiteRun.requestedNodes[0] === suiteRun.suiteNode) {
            continue;
        }

        if (!suiteRun) {
            queuedRuns.set(testNode.parent.id, { requestedNodes: [testNode], suiteNode: testNode.parent });
            continue;
        }

        if (!suiteRun.requestedNodes.includes(testNode)) {
            suiteRun.requestedNodes.push(testNode);
        }
    }

    return Array.from(queuedRuns.values());
}
