"use strict";

import * as fs from "fs";
import { exec } from "child_process";
import { Position, Range, TextDocument, Uri } from "vscode";
import { ICommand } from "./interfaces";
import { Constants } from "./constants";

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
        fs.readFile(file, "utf-8", (error, content) => {
            if (error) {
                reject(error);
            }

            resolve(content);
        });
    });
}

export async function exists(path: string): Promise<boolean> {
    return fs.promises
        .access(path, fs.constants.F_OK)
        .then(() => true)
        .catch(() => false);
}

export function changeUriScheme(uri: Uri, scheme: string): Uri {
    if (uri.scheme === scheme) {
        return uri;
    }
    const uriStr = uri.toString().replace(uri.scheme, scheme);
    const resultUri = Uri.parse(uriStr);
    return resultUri;
}

export function getCommands(command: string): ICommand {
    return {
        external: `gls.${command}`,
        internal: `galaxytools.${command}`,
    };
}

export function isGalaxyToolDocument(document: TextDocument): boolean {
    return (
        document.uri.path.endsWith(`.${Constants.TOOL_DOCUMENT_EXTENSION}`) &&
        document.languageId === Constants.LANGUAGE_ID
    );
}

/**
 * Utility class for wrapping strings with ANSI
 * scape codes.
 * Used for terminal text coloring.
 */
export abstract class OutputHighlight {
    private static readonly Black = 30;
    private static readonly Red = 31;
    private static readonly Green = 32;
    private static readonly Yellow = 33;
    private static readonly Blue = 34;
    private static readonly Magenta = 35;
    private static readonly Cyan = 36;
    private static readonly White = 37;

    public static black(text: string): string {
        return OutputHighlight.printColored(text, OutputHighlight.Black);
    }

    public static red(text: string): string {
        return OutputHighlight.printColored(text, OutputHighlight.Red);
    }

    public static green(text: string): string {
        return OutputHighlight.printColored(text, OutputHighlight.Green);
    }

    public static yellow(text: string): string {
        return OutputHighlight.printColored(text, OutputHighlight.Yellow);
    }

    public static blue(text: string): string {
        return OutputHighlight.printColored(text, OutputHighlight.Blue);
    }

    public static magenta(text: string): string {
        return OutputHighlight.printColored(text, OutputHighlight.Magenta);
    }

    public static cyan(text: string): string {
        return OutputHighlight.printColored(text, OutputHighlight.Cyan);
    }

    public static white(text: string): string {
        return OutputHighlight.printColored(text, OutputHighlight.White);
    }

    private static printColored(text: string, color: number): string {
        return `\u001b[${color}m${text}\u001b[0m`;
    }
}
