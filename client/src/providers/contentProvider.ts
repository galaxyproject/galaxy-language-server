import { commands, TextDocumentContentProvider, Uri } from "vscode";
import { Commands, GeneratedExpandedDocument } from "../commands";

export class GalaxyToolsExpadedDocumentContentProvider implements TextDocumentContentProvider {

    async provideTextDocumentContent(uri: Uri): Promise<string> {
        const result = await commands.executeCommand<GeneratedExpandedDocument>(Commands.GENERATE_EXPANDED_DOCUMENT, uri)
        if (result === undefined) {
            return "Can not expand the requested document."
        }
        return result.content;
    }
};
