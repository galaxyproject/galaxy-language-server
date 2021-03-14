'use strict';

import { ExtensionContext, workspace } from "vscode";
import { LanguageClient } from "vscode-languageclient";
import { IConfigurationFactory } from "../configuration";
import { registerConfigTreeDataProvider } from "./configurationView";


export function registerViews(client: LanguageClient, context: ExtensionContext, configFactory: IConfigurationFactory) {

    const configTreeDataProvider = registerConfigTreeDataProvider(context, configFactory);

    context.subscriptions.push(workspace.onDidChangeConfiguration(async configurationChange => {
        const sectionsToReload = [
            'galaxyTools.planemo.envPath',
            'galaxyTools.planemo.galaxyRoot',
        ];

        const needsReload = sectionsToReload.some(
            section => configurationChange.affectsConfiguration(section));
        if (needsReload) {
            configTreeDataProvider.refresh();
        }
    }));
}
