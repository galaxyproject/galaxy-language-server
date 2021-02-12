'use strict';

import { WorkspaceFolder, Event, EventEmitter, workspace, window, TextDocument } from "vscode";
import { RetireEvent, TestAdapter, TestEvent, TestLoadFinishedEvent, TestLoadStartedEvent, TestRunFinishedEvent, TestRunStartedEvent, TestSuiteEvent, TestSuiteInfo } from "vscode-test-adapter-api";
import { LANGUAGE_ID, TOOL_DOCUMENT_EXTENSION } from "../../constants";
import { TestState } from "../../testing/common";
import { ITestRunner } from "../../testing/testRunner";
import { ITestsProvider } from "../../testing/testsProvider";
import { IConfigurationFactory } from "../configuration";


export class PlanemoTestAdapter implements TestAdapter {
    private isLoading = false;

    private disposables: { dispose(): void }[] = [];
    private readonly testsByFilename = new Map<string, TestSuiteInfo>();
    private readonly testsSuitesById = new Map<string, TestSuiteInfo>();

    private readonly testsEmitter = new EventEmitter<TestLoadStartedEvent | TestLoadFinishedEvent>();
    private readonly testStatesEmitter = new EventEmitter<TestRunStartedEvent | TestRunFinishedEvent | TestSuiteEvent | TestEvent>();
    private readonly retireEmitter = new EventEmitter<RetireEvent>();

    get tests(): Event<TestLoadStartedEvent | TestLoadFinishedEvent> { return this.testsEmitter.event; }
    get testStates(): Event<TestRunStartedEvent | TestRunFinishedEvent | TestSuiteEvent | TestEvent> { return this.testStatesEmitter.event; }
    get retire(): Event<RetireEvent> { return this.retireEmitter.event; }

    constructor(
        public readonly workspaceFolder: WorkspaceFolder,
        private readonly testsProvider: ITestsProvider,
        private readonly testRunner: ITestRunner,
        private readonly configurationFactory: IConfigurationFactory,
    ) {

        this.disposables = [
            this.testsEmitter,
            this.testStatesEmitter,
            this.retireEmitter
        ];

        this.registerActions();
    }

    private registerActions() {
        this.disposables.push(workspace.onDidChangeConfiguration(async configurationChange => {
            const sectionsToReload = [
                'galaxyTools.planemo.enabled',
                'galaxyTools.planemo.virtualEnv',
                'galaxyTools.planemo.galaxyRoot',
                'galaxyTools.planemo.testing.enabled',
            ];

            const needsReload = sectionsToReload.some(
                section => configurationChange.affectsConfiguration(section, this.workspaceFolder.uri));
            if (needsReload) {
                this.load();
            }
        }));

        this.disposables.push(workspace.onDidSaveTextDocument(async document => {
            const config = this.configurationFactory.getConfiguration();
            if (config.planemo().testing().autoTestDiscoverOnSaveEnabled()) {
                const filename = document.fileName;
                if (this.testsByFilename.has(filename)) {
                    await this.load();
                }
            }
        }));

        this.disposables.push(workspace.onDidOpenTextDocument(async document => {
            if (this.isToolDocument(document)) {
                await this.load();
            }
        }));

        this.disposables.push(workspace.onDidCloseTextDocument(async document => {
            if (this.isToolDocument(document)) {
                await this.load();
            }
        }));
    }

    async load(): Promise<void> {

        if (this.isLoading) return;

        this.testsEmitter.fire(<TestLoadStartedEvent>{ type: 'started' });

        this.testsSuitesById.clear();
        this.testsByFilename.clear();

        const planemoConfig = this.configurationFactory.getConfiguration().planemo();

        if (!planemoConfig.testing().enabled()) {
            const errorMessage = "Planemo testing is disabled in the configuration."
            this.testsEmitter.fire(<TestLoadFinishedEvent>{ type: 'finished', uite: undefined, errorMessage: errorMessage });
            return;
        }
        const validationResult = planemoConfig.Validate();
        if (validationResult.hasErrors()) {
            const errorMessage = validationResult.getErrorsAsString()
            this.testsEmitter.fire(<TestLoadFinishedEvent>{ type: 'finished', uite: undefined, errorMessage: errorMessage });
            return;
        }

        try {
            const loadedTests = await this.testsProvider.discoverTests();
            this.saveToMap(loadedTests)

            this.testsEmitter.fire(<TestLoadFinishedEvent>{ type: 'finished', suite: loadedTests });

        } catch (error) {
            this.testsEmitter.fire(<TestLoadFinishedEvent>{ type: 'finished', suite: undefined, errorMessage: error.stack });
        }
        this.retireEmitter.fire({});

        this.isLoading = false;
    }

    async run(tests: string[]): Promise<void> {

        if (this.testRunner.isRunning()) return;

        const planemoConfig = this.configurationFactory.getConfiguration().planemo();
        const validationResult = planemoConfig.Validate();
        if (validationResult.hasErrors()) {
            window.showErrorMessage(validationResult.getErrorsAsString());
            return;
        }

        try {

            this.testStatesEmitter.fire(<TestRunStartedEvent>{ type: 'started', tests });

            if (tests.includes('root')) {
                tests = Array.from(this.testsSuitesById.keys());
            }

            const testRuns = tests.map(async test => {
                const testSuite = this.testsSuitesById.get(test);
                if (testSuite !== undefined) {
                    try {
                        this.setTestStatesRecursive(testSuite, 'running');
                        const states = await this.testRunner.run(planemoConfig, testSuite);
                        return states.forEach(state => {
                            const testId = state.test as string;

                            const suite = this.testsSuitesById.get(testId)
                            if (suite !== undefined) {
                                this.setTestStatesRecursive(suite, state.state, state.message);
                            } else {
                                this.testStatesEmitter.fire(state);
                            }
                        });
                    } catch (reason) {
                        this.setTestStatesRecursive(testSuite, 'failed', reason);
                    }
                }
            });
            await Promise.all(testRuns);
        } finally {
            this.testStatesEmitter.fire(<TestRunFinishedEvent>{ type: 'finished' });
        }
    }

    cancel(): void {
        this.testRunner.cancel();
    }

    dispose(): void {
        this.cancel();
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
        this.disposables = [];
    }

    private saveToMap(testSuite: TestSuiteInfo | undefined) {
        if (!testSuite) return;
        if (testSuite.id !== 'root') return;

        testSuite.children.forEach(child => {
            if (child.file && child.type === 'suite') {
                this.testsSuitesById.set(child.id, child);
                this.testsByFilename.set(child.file, child);
            }
        });
    }

    private setTestStatesRecursive(
        testSuite: TestSuiteInfo,
        state: TestState,
        message?: string | undefined
    ) {
        testSuite.children.forEach(child =>
            this.testStatesEmitter.fire(<TestEvent>{
                type: 'test',
                test: child.id,
                state,
                message,
            }));
    }

    private isToolDocument(document: TextDocument): boolean {
        return document.languageId === LANGUAGE_ID
            && document.fileName.endsWith(TOOL_DOCUMENT_EXTENSION);
    }
}
