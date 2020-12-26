'use strict';

import { window, Position, SnippetString, Range } from "vscode";
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
    replace_range: Range | null
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
        if (result.replace_range) {
            const range = cloneRange(result.replace_range)
            activeEditor.insertSnippet(snippet, range);
        }
        else {
            const position = new Position(result.position.line, result.position.character)
            activeEditor.insertSnippet(snippet, position);
        }

    } catch (err) {
        window.showErrorMessage(err);
    }
}

/**
 * Returns a new instance of the given immutable Range.
 * @param range The original Range
 */
export function cloneRange(range: Range): Range {
    let line = range.start.line;
    let character = range.start.character;
    let startPosition = new Position(line, character);
    line = range.end.line;
    character = range.end.character;
    let endPosition = new Position(line, character);
    return new Range(startPosition, endPosition);
}