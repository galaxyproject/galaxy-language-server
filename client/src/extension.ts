"use strict";

import * as net from "net";
import { ExtensionContext, ExtensionMode, IndentAction, LanguageConfiguration, languages, window } from "vscode";
import { LanguageClient, LanguageClientOptions, ServerOptions } from "vscode-languageclient/node";
import { setupCommands } from "./commands";
import { Constants } from "./constants";
import { DefaultConfigurationFactory } from "./planemo/configuration";
import { setupPlanemo } from "./planemo/main";
import { setupProviders } from "./providers/setup";
import { installLanguageServer } from "./setup";
import { logger } from "./logger";

let client: LanguageClient;

/**
 * This method gets called when the extension gets activated for the first time.
 * @param context The extension context
 */
export async function activate(context: ExtensionContext) {
    const configFactory = new DefaultConfigurationFactory();
    if (context.extensionMode === ExtensionMode.Development) {
        logger.info("Extension activated in DEV mode");
        // Development - Connect to language server (already running) using TCP
        client = connectToLanguageServerTCP(2087);
    } else {
        // Production - Install (first time only), launch and connect to language server.
        logger.info("Extension activated in PRODUCTION mode");
        try {
            const isSilentInstall = configFactory.getConfiguration().server().silentInstall();
            const python = await installLanguageServer(context, isSilentInstall);
            if (python === undefined) {
                // The language server could not be installed
                return;
            }

            client = startLanguageServer(python, ["-m", Constants.GALAXY_LS], context.extensionPath);
        } catch (err: any) {
            logger.error(`Extension activation failed: ${err}`);
            window.showErrorMessage(err);
        }
    }

    // Configure auto-indentation
    languages.setLanguageConfiguration(Constants.LANGUAGE_ID, getIndentationRules());
    logger.debug("Configured auto-indentation rules for Galaxy Tool XML");

    context.subscriptions.push(client.start());
    logger.info("Language client started successfully");

    setupCommands(client, context);
    logger.debug("Commands registered");

    setupProviders(client, context);
    logger.debug("Providers registered");

    client.onReady().then(() => {
        logger.info("Language server is ready");
        setupPlanemo(client, context, configFactory);
    });
}

/**
 * Release resources when the extension gets deactivated.
 */
export function deactivate(): Thenable<void> {
    return client ? client.stop() : Promise.resolve();
}

function getClientOptions(): LanguageClientOptions {
    return {
        // Register the server for xml documents
        documentSelector: [
            { scheme: "file", language: Constants.LANGUAGE_ID },
            { scheme: "untitled", language: Constants.LANGUAGE_ID },
        ],
        outputChannel: logger.getOutputChannel(),
        synchronize: {},
    };
}

/**
 * Returns a LanguageClient instance that will connect to a Language Server running on localhost using the given port.
 * @param port The port where the server is listening
 */
function connectToLanguageServerTCP(port: number, maxRetries = 5, retryDelayMs = 1000): LanguageClient {
    let attempt = 0;
    const serverOptions: ServerOptions = () => {
        return new Promise((resolve, reject) => {
            function tryConnect() {
                const clientSocket = new net.Socket();
                clientSocket.connect(port, "127.0.0.1", () => {
                    logger.debug(`Connected to language server on port ${port}`);
                    resolve({
                        reader: clientSocket,
                        writer: clientSocket,
                    });
                });
                clientSocket.on("error", (err) => {
                    clientSocket.destroy();
                    attempt++;
                    if (attempt < maxRetries) {
                        logger.debug(`Connection to language server failed (attempt ${attempt}). Retrying in ${retryDelayMs}ms...`);
                        setTimeout(tryConnect, retryDelayMs);
                    } else {
                        logger.error(`Could not connect to language server after ${maxRetries} attempts.`);
                        reject(err);
                    }
                });
            }
            tryConnect();
        });
    };

    return new LanguageClient(`galaxy language server tcp (port ${port})`, serverOptions, getClientOptions());
}

/**
 * Launches the language server using the specified Python command.
 * @param command The Python path in the virtual environment
 * @param args The arguments to launch the language server
 * @param cwd The extension's path
 */
function startLanguageServer(command: string, args: string[], cwd: string): LanguageClient {
    const serverOptions: ServerOptions = {
        args,
        command,
        options: { cwd },
    };

    logger.info(`Starting Galaxy Language Server with command: ${command} ${args.join(" ")} in ${cwd}`);

    return new LanguageClient(command, serverOptions, getClientOptions());
}

/**
 * Defines the rules for auto-indentation.
 * From: https://github.com/redhat-developer/vscode-xml/blob/027c492f8c137682a2432a2f27046ccd260e63a3/src/extension.ts#L458
 */
function getIndentationRules(): LanguageConfiguration {
    return {
        indentationRules: {
            increaseIndentPattern:
                /<(?!\?|[^>]*\/>)([-_\.A-Za-z0-9]+)(?=\s|>)\b[^>]*>(?!.*<\/\1>)|<!--(?!.*-->)|\{[^}"']*$/,
            decreaseIndentPattern: /^\s*(<\/[-_\.A-Za-z0-9]+\b[^>]*>|-->|\})/,
        },
        onEnterRules: [
            {
                beforeText: new RegExp(`<([_:\\w][_:\\w-.\\d]*)([^/>]*(?!/)>)[^<]*$`, "i"),
                afterText: /^<\/([_:\w][_:\w-.\d]*)\s*>/i,
                action: { indentAction: IndentAction.IndentOutdent },
            },
            {
                beforeText: new RegExp(`<(\\w[\\w\\d]*)([^/>]*(?!/)>)[^<]*$`, "i"),
                action: { indentAction: IndentAction.Indent },
            },
        ],
    };
}
