"use strict";

import {
    window,
    Position,
    SnippetString,
    Range,
    ExtensionContext,
    commands,
    TextEditor,
    Uri,
    workspace,
    ViewColumn,
    TextDocument,
} from "vscode";
import { LanguageClient } from "vscode-languageclient/node";
import { Constants } from "./constants";
import { ICommand } from "./interfaces";
import { GalaxyToolsExpadedDocumentContentProvider } from "./providers/contentProvider";
import { activateTagClosing, AutoCloseTagResult } from "./tagClosing";
import { changeUriScheme, cloneRange, getCommands } from "./utils";
import { DirectoryTreeItem } from "./views/common";

export namespace Commands {
    export const AUTO_CLOSE_TAGS: ICommand = getCommands("completion.autoCloseTags");
    export const GENERATE_TEST: ICommand = getCommands("generate.tests");
    export const GENERATE_COMMAND: ICommand = getCommands("generate.command");
    export const SORT_SINGLE_PARAM_ATTRS: ICommand = getCommands("sort.singleParamAttributes");
    export const SORT_DOCUMENT_PARAMS_ATTRS: ICommand = getCommands("sort.documentParamsAttributes");
    export const DISCOVER_TESTS_IN_WORKSPACE: ICommand = getCommands("tests.discoverInWorkspace");
    export const DISCOVER_TESTS_IN_DOCUMENT: ICommand = getCommands("tests.discoverInDocument");
    export const PLANEMO_OPEN_SETTINGS: ICommand = getCommands("planemo.openSettings");
    export const OPEN_TERMINAL_AT_DIRECTORY_ITEM: ICommand = getCommands("openTerminalAtDirectory");
    export const GENERATE_EXPANDED_DOCUMENT: ICommand = getCommands("generate.expandedDocument");
    export const PREVIEW_EXPANDED_DOCUMENT: ICommand = getCommands("preview.expandedDocument");
}

interface GeneratedSnippetResult {
    snippet: string;
    position: Position;
    replace_range: Range | null;
    error_message: string;
}

interface ReplaceTextRangeResult {
    text: string;
    replace_range: Range;
}

export interface GeneratedExpandedDocument {
    content: string;
    error_message: string;
}

export function setupCommands(client: LanguageClient, context: ExtensionContext) {
    setupAutoCloseTags(client, context);

    setupGenerateTestCases(client, context);

    setupGenerateCommandSection(client, context);

    setupSortSingleParamAttributes(client, context);

    setupSortDocumentParams(client, context);

    setupGenerateExpandedDocument(client, context);

    context.subscriptions.push(
        commands.registerCommand(Commands.PREVIEW_EXPANDED_DOCUMENT.internal, previewExpandedDocument)
    );

    context.subscriptions.push(commands.registerCommand(Commands.PLANEMO_OPEN_SETTINGS.internal, openPlanemoSettings));

    context.subscriptions.push(
        commands.registerCommand(Commands.OPEN_TERMINAL_AT_DIRECTORY_ITEM.internal, (item: DirectoryTreeItem) =>
            openTerminalAtDirectoryItem(item)
        )
    );

    notifyExtensionActive();
}

function setupGenerateExpandedDocument(client: LanguageClient, context: ExtensionContext) {
    const generateExpandedDocument = async (uri: Uri) => {
        return requestExpandedDocument(uri, client);
    };
    context.subscriptions.push(
        commands.registerCommand(Commands.GENERATE_EXPANDED_DOCUMENT.internal, generateExpandedDocument)
    );
}

function setupSortDocumentParams(client: LanguageClient, context: ExtensionContext) {
    const sortDocumentParamsAttrs = async () => {
        requestSortDocumentParamsAttrs(client, Commands.SORT_DOCUMENT_PARAMS_ATTRS.external);
    };
    context.subscriptions.push(
        commands.registerCommand(Commands.SORT_DOCUMENT_PARAMS_ATTRS.internal, sortDocumentParamsAttrs)
    );
}

function setupSortSingleParamAttributes(client: LanguageClient, context: ExtensionContext) {
    const sortSingleParamAttrs = async () => {
        requestSortSingleParamAttrs(client, Commands.SORT_SINGLE_PARAM_ATTRS.external);
    };
    context.subscriptions.push(
        commands.registerCommand(Commands.SORT_SINGLE_PARAM_ATTRS.internal, sortSingleParamAttrs)
    );
}

function setupGenerateCommandSection(client: LanguageClient, context: ExtensionContext) {
    const generateCommand = async () => {
        requestInsertSnippet(client, Commands.GENERATE_COMMAND.external);
    };
    context.subscriptions.push(commands.registerCommand(Commands.GENERATE_COMMAND.internal, generateCommand));
}

function setupGenerateTestCases(client: LanguageClient, context: ExtensionContext) {
    const generateTest = async () => {
        requestInsertSnippet(client, Commands.GENERATE_TEST.external);
    };
    context.subscriptions.push(commands.registerCommand(Commands.GENERATE_TEST.internal, generateTest));
}

function setupAutoCloseTags(client: LanguageClient, context: ExtensionContext) {
    const tagProvider = async (document: TextDocument, position: Position) => {
        let param = client.code2ProtocolConverter.asTextDocumentPositionParams(document, position);
        let text = (await commands.executeCommand(Commands.AUTO_CLOSE_TAGS.external, param)) as AutoCloseTagResult;
        return text;
    };
    context.subscriptions.push(activateTagClosing(tagProvider));
}

async function requestSortSingleParamAttrs(client: LanguageClient, command: string) {
    const activeEditor = window.activeTextEditor;
    if (!activeEditor) return;

    const isSaved = ensureDocumentIsSaved(activeEditor);
    if (!isSaved) return;

    const document = activeEditor.document;

    const position = activeEditor.selection.active;
    const param = client.code2ProtocolConverter.asTextDocumentPositionParams(document, position);
    const response = (await commands.executeCommand(command, param)) as ReplaceTextRangeResult;
    if (!response) return;

    try {
        const range = cloneRange(response.replace_range);
        activeEditor.edit((builder) => {
            builder.replace(range, response.text);
        });
    } catch (err: any) {
        window.showErrorMessage(err);
    }
}

async function requestSortDocumentParamsAttrs(client: LanguageClient, command: string) {
    const activeEditor = window.activeTextEditor;
    if (!activeEditor) return;

    const isSaved = ensureDocumentIsSaved(activeEditor);
    if (!isSaved) return;

    const document = activeEditor.document;

    const param = client.code2ProtocolConverter.asTextDocumentIdentifier(document);
    const response = (await commands.executeCommand(command, param)) as Array<ReplaceTextRangeResult>;
    if (!response) return;

    try {
        activeEditor.edit((builder) => {
            for (let index = 0; index < response.length; index++) {
                const element = response[index];
                const range = cloneRange(element.replace_range);
                builder.replace(range, element.text);
            }
        });
    } catch (err: any) {
        window.showErrorMessage(err);
    }
}

async function requestInsertSnippet(client: LanguageClient, command: string) {
    const activeEditor = window.activeTextEditor;
    if (!activeEditor) return;

    const isSaved = ensureDocumentIsSaved(activeEditor);
    if (!isSaved) return;

    const document = activeEditor.document;

    const param = client.code2ProtocolConverter.asTextDocumentIdentifier(document);
    const response = (await commands.executeCommand(command, param)) as GeneratedSnippetResult;
    if (!response || !response.snippet || response.error_message) {
        if (response.error_message) {
            window.showErrorMessage(response.error_message);
        }
        return;
    }

    try {
        const snippet = new SnippetString(response.snippet);
        if (response.replace_range) {
            const range = cloneRange(response.replace_range);
            activeEditor.insertSnippet(snippet, range);
        } else {
            const position = new Position(response.position.line, response.position.character);
            activeEditor.insertSnippet(snippet, position);
        }
    } catch (err: any) {
        window.showErrorMessage(err);
    }
}

function ensureDocumentIsSaved(editor: TextEditor): Boolean {
    if (editor.document.isDirty) {
        window.showErrorMessage("Please save the document before executing this action.");
    }
    return !editor.document.isDirty;
}

function openPlanemoSettings() {
    commands.executeCommand("workbench.action.openSettings", "galaxyTools.planemo");
}

function openTerminalAtDirectoryItem(item: DirectoryTreeItem) {
    const terminal = window.createTerminal({
        cwd: item.directoryUri.fsPath,
    });
    terminal.show(false);
}

function notifyExtensionActive() {
    commands.executeCommand("setContext", "galaxytools:isActive", true);
}

async function requestExpandedDocument(
    uri: Uri,
    client: LanguageClient
): Promise<GeneratedExpandedDocument | undefined> {
    const document = await workspace.openTextDocument(uri);
    const param = client.code2ProtocolConverter.asTextDocumentIdentifier(document);
    const response = (await commands.executeCommand(
        Commands.GENERATE_EXPANDED_DOCUMENT.external,
        param
    )) as GeneratedExpandedDocument;
    if (!response || response.error_message) {
        if (response.error_message) {
            window.showErrorMessage(response.error_message);
        }
        return undefined;
    }
    return response;
}

function convertToExpandedDocumentUri(fileUri: Uri) {
    const uri = changeUriScheme(fileUri, Constants.EXPAND_DOCUMENT_SCHEMA);
    const finalUri = Uri.parse(`${uri}${Constants.EXPAND_DOCUMENT_URI_SUFFIX}`);
    return finalUri;
}

async function previewExpandedDocument() {
    const activeEditor = window.activeTextEditor;
    if (!activeEditor) return;
    const isSaved = ensureDocumentIsSaved(activeEditor);
    if (!isSaved) return;

    const document = activeEditor.document;
    if (document.uri.scheme === Constants.EXPAND_DOCUMENT_SCHEMA || document.languageId !== Constants.LANGUAGE_ID) {
        return;
    }
    const expandedDocumentUri = convertToExpandedDocumentUri(document.uri);
    GalaxyToolsExpadedDocumentContentProvider.getInstance().update(expandedDocumentUri);
    const doc = await workspace.openTextDocument(expandedDocumentUri);
    await window.showTextDocument(doc, { preview: false, viewColumn: ViewColumn.Beside });
}
