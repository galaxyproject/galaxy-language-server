"use strict";

import { ExtensionContext } from "vscode";
import { LanguageClient } from "vscode-languageclient/node";
import { IConfigurationFactory } from "./configuration";
import { setupTesting } from "./testing/main";
import { registerViews } from "./views/main";

export function setupPlanemo(client: LanguageClient, context: ExtensionContext, configFactory: IConfigurationFactory) {
    registerViews(client, context, configFactory);

    setupTesting(client, context, configFactory);
}
