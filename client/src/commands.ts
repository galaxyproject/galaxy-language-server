'use strict';

import { window, Position, SnippetString, Range, ExtensionContext, commands } from "vscode";
import { RequestType, TextDocumentIdentifier, TextDocumentPositionParams, LanguageClient } from "vscode-languageclient";
import { cloneRange } from "./utils";

export namespace Commands {

    export const AUTO_CLOSE_TAGS = 'galaxytools.completion.autoCloseTags';
    export const GENERATE_TEST = 'galaxytools.generate.tests';
    export const GENERATE_COMMAND = 'galaxytools.generate.command';
    export const SORT_SINGLE_PARAM_ATTRS = 'galaxytools.sort.singleParamAttributes';
}

namespace GeneratedTestRequest {
    export const type: RequestType<TextDocumentIdentifier, GeneratedSnippetResult, any, any> = new RequestType(Commands.GENERATE_TEST);
}

namespace GeneratedCommandRequest {
    export const type: RequestType<TextDocumentIdentifier, GeneratedSnippetResult, any, any> = new RequestType(Commands.GENERATE_COMMAND);
}

namespace SortSingleParamAttrsCommandRequest {
    export const type: RequestType<TextDocumentPositionParams, ReplaceTextRangeResult, any, any> = new RequestType(Commands.SORT_SINGLE_PARAM_ATTRS);
}
interface GeneratedSnippetResult {
    snippet: string,
    position: Position
    replace_range: Range | null
}

interface ReplaceTextRangeResult {
    text: string,
    replace_range: Range
}



export function setupCommands(client: LanguageClient, context: ExtensionContext) {
    // Setup generate test command
    const generateTest = async () => {
        requestInsertSnippet(client, GeneratedTestRequest.type)
    };
    context.subscriptions.push(commands.registerCommand(Commands.GENERATE_TEST, generateTest));

    // Setup generate command section command
    const generateCommand = async () => {
        requestInsertSnippet(client, GeneratedCommandRequest.type)
    };
    context.subscriptions.push(commands.registerCommand(Commands.GENERATE_COMMAND, generateCommand));

    // Setup sort param attributes command
    const sortSingleParamAttrs = async () => {
        requestSortSingleParamAttrs(client, SortSingleParamAttrsCommandRequest.type)
    };
    context.subscriptions.push(commands.registerCommand(Commands.SORT_SINGLE_PARAM_ATTRS, sortSingleParamAttrs));

}

async function requestSortSingleParamAttrs(client: LanguageClient, request: RequestType<TextDocumentPositionParams, ReplaceTextRangeResult, any, any>) {
    let activeEditor = window.activeTextEditor;
    if (!activeEditor) return;

    if (activeEditor.document.isDirty) {
        window.showErrorMessage("Please save the document before executing this action.");
        return;
    }
    let document = activeEditor.document;

    const position = activeEditor.selection.active;
    let param = client.code2ProtocolConverter.asTextDocumentPositionParams(document, position);
    let result = await client.sendRequest(request, param);
    if (!result) return;

    try {
        const range = cloneRange(result.replace_range)
        activeEditor.edit(builder => {
            builder.replace(range, result.text);
        });

    } catch (err) {
        window.showErrorMessage(err);
    }
}

async function requestInsertSnippet(client: LanguageClient, request: RequestType<TextDocumentIdentifier, GeneratedSnippetResult, any, any>) {
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