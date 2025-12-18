/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *
 *  Based on: https://github.com/redhat-developer/vscode-xml/blob/master/src/tagClosing.ts
 *--------------------------------------------------------------------------------------------*/
"use strict";

import {
    window,
    workspace,
    Disposable,
    TextDocumentContentChangeEvent,
    TextDocument,
    Position,
    SnippetString,
    Range,
} from "vscode";
import { cloneRange } from "./utils";
export interface AutoCloseTagResult {
    snippet: string;
    range: Range;
}

export function activateTagClosing(
    tagProvider: (document: TextDocument, position: Position) => Thenable<AutoCloseTagResult>
): Disposable {
    const TRIGGER_CHARACTERS = [">", "/"];
    let disposables: Disposable[] = [];
    workspace.onDidChangeTextDocument(
        (event) => onDidChangeTextDocument(event.document, event.contentChanges),
        null,
        disposables
    );

    let timeout: NodeJS.Timer | undefined = void 0;

    function onDidChangeTextDocument(document: TextDocument, changes: ReadonlyArray<TextDocumentContentChangeEvent>) {
        let activeDocument = window.activeTextEditor && window.activeTextEditor.document;
        if (document !== activeDocument || changes.length === 0) {
            return;
        }
        if (typeof timeout !== "undefined") {
            clearTimeout(timeout);
        }
        let lastChange = changes[changes.length - 1];
        let lastCharacter = lastChange.text[lastChange.text.length - 1];
        if (lastChange.rangeLength > 0 || lastChange.text.length > 1 || TRIGGER_CHARACTERS.indexOf(lastCharacter) < 0) {
            return;
        }
        let rangeStart = lastChange.range.start;
        let version = document.version;
        timeout = setTimeout(() => {
            let position = new Position(rangeStart.line, rangeStart.character + lastChange.text.length);
            tagProvider(document, position).then(
                (result) => {
                    if (!result) {
                        return;
                    }
                    let text = result.snippet;
                    let replaceLocation: Position | Range;
                    let range: Range = result.range;
                    if (range != null) {
                        replaceLocation = cloneRange(range);
                    } else {
                        replaceLocation = position;
                    }
                    if (text) {
                        let activeEditor = window.activeTextEditor;
                        if (activeEditor) {
                            let activeDocument = activeEditor.document;
                            if (document === activeDocument && activeDocument.version === version) {
                                activeEditor.insertSnippet(new SnippetString(text), replaceLocation);
                            }
                        }
                    }
                },
                (reason: any) => {
                    // Tag closing cancelled, this is a normal flow and doesn't need logging
                }
            );
            timeout = void 0;
        }, 100);
    }
    return Disposable.from(...disposables);
}
