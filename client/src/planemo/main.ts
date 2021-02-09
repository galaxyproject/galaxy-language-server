'use strict';

import { ExtensionContext } from "vscode";
import { LanguageClient } from "vscode-languageclient";
import { IConfigurationFactory } from "./configuration";
import { setupTesting } from "./testing/main";


export function setupPlanemo(client: LanguageClient, context: ExtensionContext, configFactory: IConfigurationFactory) {
    setupTesting(client, context, configFactory);
}
