'use strict';

import { window, Position, SnippetString, Range, ExtensionContext, commands, TextEditor } from "vscode";
import { RequestType, TextDocumentIdentifier, TextDocumentPositionParams, LanguageClient } from "vscode-languageclient";
import { cloneRange } from "./utils";

export namespace Commands {

    export const AUTO_CLOSE_TAGS = 'galaxytools.completion.autoCloseTags';
    export const GENERATE_TEST = 'galaxytools.generate.tests';
    export const GENERATE_COMMAND = 'galaxytools.generate.command';
    export const SORT_SINGLE_PARAM_ATTRS = 'galaxytools.sort.singleParamAttributes';
    export const SORT_DOCUMENT_PARAMS_ATTRS = 'galaxytools.sort.documentParamsAttributes';
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

namespace SortDocumentParamsAttrsCommandRequest {
    export const type: RequestType<TextDocumentIdentifier, Array<ReplaceTextRangeResult>, any, any> = new RequestType(Commands.SORT_DOCUMENT_PARAMS_ATTRS);
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

    // Setup sort all document param attributes command
    const sortDocumentParamsAttrs = async () => {
        requestSortDocumentParamsAttrs(client, SortDocumentParamsAttrsCommandRequest.type)
    };
    context.subscriptions.push(commands.registerCommand(Commands.SORT_DOCUMENT_PARAMS_ATTRS, sortDocumentParamsAttrs));
}

async function requestSortSingleParamAttrs(client: LanguageClient, request: RequestType<TextDocumentPositionParams, ReplaceTextRangeResult, any, any>) {
    let activeEditor = window.activeTextEditor;
    if (!activeEditor) return;

    const isSaved = ensureDocumentIsSaved(activeEditor);
    if (!isSaved) return;

    let document = activeEditor.document;

    const position = activeEditor.selection.active;
    let param = client.code2ProtocolConverter.asTextDocumentPositionParams(document, position);
    let response = await client.sendRequest(request, param);
    if (!response) return;

    try {
        const range = cloneRange(response.replace_range)
        activeEditor.edit(builder => {
            builder.replace(range, response.text);
        });

    } catch (err) {
        window.showErrorMessage(err);
    }
}

async function requestSortDocumentParamsAttrs(client: LanguageClient, request: RequestType<TextDocumentIdentifier, Array<ReplaceTextRangeResult>, any, any>) {
    let activeEditor = window.activeTextEditor;
    if (!activeEditor) return;

    const isSaved = ensureDocumentIsSaved(activeEditor);
    if (!isSaved) return;

    let document = activeEditor.document;

    let param = client.code2ProtocolConverter.asTextDocumentIdentifier(document);
    let response = await client.sendRequest(request, param);
    if (!response) return;

    try {
        activeEditor.edit(builder => {
            for (let index = 0; index < response.length; index++) {
                const element = response[index];
                const range = cloneRange(element.replace_range)
                builder.replace(range, element.text);
            }
        });

    } catch (err) {
        window.showErrorMessage(err);
    }
}

async function requestInsertSnippet(client: LanguageClient, request: RequestType<TextDocumentIdentifier, GeneratedSnippetResult, any, any>) {
    let activeEditor = window.activeTextEditor;
    if (!activeEditor) return;

    const isSaved = ensureDocumentIsSaved(activeEditor);
    if (!isSaved) return;

    let document = activeEditor.document;

    let param = client.code2ProtocolConverter.asTextDocumentIdentifier(document);
    let response = await client.sendRequest(request, param);
    if (!response || !response.snippet) return;

    try {
        const snippet = new SnippetString(response.snippet);
        if (response.replace_range) {
            const range = cloneRange(response.replace_range)
            activeEditor.insertSnippet(snippet, range);
        }
        else {
            const position = new Position(response.position.line, response.position.character)
            activeEditor.insertSnippet(snippet, position);
        }

    } catch (err) {
        window.showErrorMessage(err);
    }
}

function ensureDocumentIsSaved(editor: TextEditor): Boolean {
    if (editor.document.isDirty) {
        window.showErrorMessage("Please save the document before executing this action.");
    }
    return !editor.document.isDirty;
}