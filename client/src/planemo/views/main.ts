"use strict";

import { ExtensionContext, workspace } from "vscode";
import { LanguageClient } from "vscode-languageclient/node";
import { Settings } from "../../configuration/workspaceConfiguration";
import { IConfigurationFactory } from "../configuration";
import { registerConfigTreeDataProvider } from "./configurationView";

export function registerViews(client: LanguageClient, context: ExtensionContext, configFactory: IConfigurationFactory) {
    const configTreeDataProvider = registerConfigTreeDataProvider(context, configFactory);

    context.subscriptions.push(
        workspace.onDidChangeConfiguration(async (configurationChange) => {
            const sectionsToReload = [Settings.Planemo.ENV_PATH, Settings.Planemo.GALAXY_ROOT];

            const needsReload = sectionsToReload.some((section) => configurationChange.affectsConfiguration(section));
            if (needsReload) {
                configTreeDataProvider.refresh();
            }
        })
    );
}
