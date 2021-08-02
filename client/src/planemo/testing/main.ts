"use strict";

import { ExtensionContext, extensions } from "vscode";
import { LanguageClient } from "vscode-languageclient/node";
import { TestHub, testExplorerExtensionId } from "vscode-test-adapter-api";
import { TestAdapterRegistrar } from "vscode-test-adapter-util";
import { LanguageServerTestProvider } from "../../testing/testsProvider";
import { IConfigurationFactory } from "../configuration";
import { PlanemoTestAdapter } from "./testAdapter";
import { PlanemoTestRunner } from "./testRunner";

export function setupTesting(client: LanguageClient, context: ExtensionContext, configFactory: IConfigurationFactory) {
    const testProvider = new LanguageServerTestProvider(client);
    const planemoTestRunner = new PlanemoTestRunner("planemo");

    // get the Test Explorer extension
    const testExplorerExtension = extensions.getExtension<TestHub>(testExplorerExtensionId);
    if (testExplorerExtension) {
        const testHub = testExplorerExtension.exports;

        context.subscriptions.push(
            new TestAdapterRegistrar(
                testHub,
                (workspaceFolder) =>
                    new PlanemoTestAdapter(workspaceFolder, testProvider, planemoTestRunner, configFactory)
            )
        );
    }
}
