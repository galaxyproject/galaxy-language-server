"use strict";

import * as fs from 'fs';
import { exec } from "child_process";
import { Position, Range } from "vscode";


export async function execAsync(command: string, options: object = {}): Promise<string> {
    return new Promise((resolve, reject) => {
        exec(command, options, (error, stdout, _) => {
            if (error) {
                return reject(error);
            }
            resolve(stdout.trim().toString());
        });
    });
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

export function readFile(file: fs.PathLike): Promise<string> {
    return new Promise<string>((resolve, reject) => {
        fs.readFile(file, 'utf-8', (error, content) => {
            if (error) {
                reject(error);
            }

            resolve(content);
        });
    });
}
