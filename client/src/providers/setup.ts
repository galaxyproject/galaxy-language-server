import { ExtensionContext, languages, workspace } from "vscode";
import { LanguageClient } from "vscode-languageclient/node";
import { Constants } from "../constants";
import { GalaxyToolsCodeActionProvider } from "./codeActions";
import { GalaxyToolsExpandedDocumentContentProvider } from "./contentProvider";

export function setupProviders(client: LanguageClient, context: ExtensionContext) {
    const codeActionProvider = new GalaxyToolsCodeActionProvider();
    context.subscriptions.push(
        languages.registerCodeActionsProvider(Constants.LANGUAGE_ID, codeActionProvider, {
            providedCodeActionKinds: GalaxyToolsCodeActionProvider.providedCodeActionKinds,
        })
    );

    const expandedDocumentProvider = GalaxyToolsExpandedDocumentContentProvider.getInstance();
    context.subscriptions.push(
        workspace.registerTextDocumentContentProvider(Constants.EXPAND_DOCUMENT_SCHEMA, expandedDocumentProvider)
    );
}
