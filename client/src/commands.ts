'use strict';

import { Position } from "vscode";
import { RequestType, TextDocumentIdentifier } from "vscode-languageclient";

export namespace Commands {

    export const AUTO_CLOSE_TAGS = 'galaxytools.completion.autoCloseTags';
    export const GENERATE_TEST = 'galaxytools.generate.test';
}


export namespace GeneratedTestRequest {
    export const type: RequestType<TextDocumentIdentifier, GeneratedTestResult, any, any> = new RequestType(Commands.GENERATE_TEST);
}

export interface GeneratedTestResult {
    snippet: string,
    position: Position
}