'use strict';

import { window, Position, SnippetString } from "vscode";
import { RequestType, TextDocumentIdentifier, LanguageClient } from "vscode-languageclient";

export namespace Commands {

    export const AUTO_CLOSE_TAGS = 'galaxytools.completion.autoCloseTags';
    export const GENERATE_TEST = 'galaxytools.generate.tests';
    export const GENERATE_COMMAND = 'galaxytools.generate.command';
}


export namespace GeneratedTestRequest {
    export const type: RequestType<TextDocumentIdentifier, GeneratedSnippetResult, any, any> = new RequestType(Commands.GENERATE_TEST);
}

export namespace GeneratedCommandRequest {
    export const type: RequestType<TextDocumentIdentifier, GeneratedSnippetResult, any, any> = new RequestType(Commands.GENERATE_COMMAND);
}

export interface GeneratedSnippetResult {
    snippet: string,
    position: Position
}

export async function requestInsertSnippet(client: LanguageClient, request: RequestType<TextDocumentIdentifier, GeneratedSnippetResult, any, any>) {
    let activeEditor = window.activeTextEditor;
    if (!activeEditor) return;

    if (activeEditor.document.isDirty) {
        window.showErrorMessage("Please save the document before executing this action.");
        return;
    }
    let document = activeEditor.document;

    let param = client.code2ProtocolConverter.asTextDocumentIdentifier(document);
    let result = await client.sendRequest(request, param);
    if (!result || !result.snippet) return;

    try {
        const snippet = new SnippetString(result.snippet);
        const position = new Position(result.position.line, result.position.character)
        activeEditor.insertSnippet(snippet, position);
    } catch (err) {
        window.showErrorMessage(err);
    }
}