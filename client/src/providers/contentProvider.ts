import { commands, Event, EventEmitter, TextDocumentContentProvider, Uri } from "vscode";
import { Commands, GeneratedExpandedDocument } from "../commands";
import { Constants } from "../constants";
import { changeUriScheme } from "../utils";

export class GalaxyToolsExpandedDocumentContentProvider implements TextDocumentContentProvider {
    private static instance: GalaxyToolsExpandedDocumentContentProvider;

    private onDidChangeEmitter = new EventEmitter<Uri>();

    private constructor() {}

    public static getInstance(): GalaxyToolsExpandedDocumentContentProvider {
        if (!this.instance) {
            this.instance = new GalaxyToolsExpandedDocumentContentProvider();
        }
        return this.instance;
    }

    async provideTextDocumentContent(uri: Uri): Promise<string> {
        const finalUri = this.convertToFileUri(uri);
        const result = await commands.executeCommand<GeneratedExpandedDocument>(
            Commands.GENERATE_EXPANDED_DOCUMENT.internal,
            finalUri
        );
        if (result === undefined) {
            return "Can not expand the requested document.";
        }
        return result.content;
    }

    get onDidChange(): Event<Uri> {
        return this.onDidChangeEmitter.event;
    }

    public update(documentUri: Uri) {
        this.onDidChangeEmitter.fire(documentUri);
    }

    private convertToFileUri(uri: Uri): Uri {
        const fileUri = changeUriScheme(uri, "file");
        const uriStr = fileUri.toString().replace(Constants.EXPAND_DOCUMENT_URI_SUFFIX, "");
        const finalUri = Uri.parse(uriStr);
        return finalUri;
    }
}
