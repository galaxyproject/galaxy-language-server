import { commands, TextDocumentContentProvider, Uri } from "vscode";
import { Commands, GeneratedExpandedDocument } from "../commands";
import { Constants } from "../constants";
import { changeUriScheme } from "../utils";

export class GalaxyToolsExpadedDocumentContentProvider implements TextDocumentContentProvider {

    async provideTextDocumentContent(uri: Uri): Promise<string> {

        const finalUri = this.convertToFileUri(uri);
        const result = await commands.executeCommand<GeneratedExpandedDocument>(Commands.GENERATE_EXPANDED_DOCUMENT, finalUri)
        if (result === undefined) {
            return "Can not expand the requested document."
        }
        return result.content;
    }

    private convertToFileUri(uri: Uri): Uri {
        const fileUri = changeUriScheme(uri, "file");
        const uriStr = fileUri.toString().replace(Constants.EXPAND_DOCUMENT_URI_SUFFIX, "")
        const finalUri = Uri.parse(uriStr);
        return finalUri;
    }
};
