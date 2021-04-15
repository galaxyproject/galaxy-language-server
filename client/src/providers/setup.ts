import { ExtensionContext, languages, workspace } from "vscode";
import { LanguageClient } from "vscode-languageclient";
import { Constants } from "../constants";
import { GalaxyToolsCodeActionProvider } from "./codeActions";
import { GalaxyToolsExpadedDocumentContentProvider } from "./contentProvider";

export function setupProviders(client: LanguageClient, context: ExtensionContext) {

    const codeActionProvider = new GalaxyToolsCodeActionProvider();
    context.subscriptions.push(
        languages.registerCodeActionsProvider(Constants.LANGUAGE_ID, codeActionProvider, {
            providedCodeActionKinds: GalaxyToolsCodeActionProvider.providedCodeActionKinds
        })
    );

    const expandedDocumentProvider = new GalaxyToolsExpadedDocumentContentProvider();
    context.subscriptions.push(
        workspace.registerTextDocumentContentProvider(Constants.EXPAND_DOCUMENT_SCHEMA, expandedDocumentProvider)
    );

}
