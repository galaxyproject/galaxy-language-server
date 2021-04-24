"use strict";

import * as net from "net";
import { ExtensionContext, window, TextDocument, Position, IndentAction, LanguageConfiguration, languages, ExtensionMode } from "vscode";
import { LanguageClient, LanguageClientOptions, ServerOptions } from "vscode-languageclient/node";
import { activateTagClosing, TagCloseRequest } from './tagClosing';
import { installLanguageServer } from './setup';
import { Constants } from './constants';
import { setupCommands } from './commands';
import { setupPlanemo } from "./planemo/main";
import { DefaultConfigurationFactory } from "./planemo/configuration";
import { setupProviders } from "./providers/setup";

let client: LanguageClient;

/**
 * This method gets called when the extension gets activated for the first time.
 * @param context The extension context
 */
export async function activate(context: ExtensionContext) {
  if (context.extensionMode === ExtensionMode.Development) {
    // Development - Connect to language server (already running) using TCP
    client = connectToLanguageServerTCP(2087);
  } else {
    // Production - Install (first time only), launch and connect to language server.
    try {

      const python = await installLanguageServer(context);
      if (python === undefined) {
        // The language server could not be installed
        return;
      }

      client = startLanguageServer(python, ["-m", Constants.GALAXY_LS], context.extensionPath);

    } catch (err) {
      window.showErrorMessage(err);
    }
  }

  // Configure auto-indentation
  languages.setLanguageConfiguration(Constants.LANGUAGE_ID, getIndentationRules());

  context.subscriptions.push(client.start());

  const configFactory = new DefaultConfigurationFactory();

  // Setup auto close tags
  const tagProvider = (document: TextDocument, position: Position) => {
    let param = client.code2ProtocolConverter.asTextDocumentPositionParams(document, position);
    let text = client.sendRequest(TagCloseRequest.type, param);
    return text;
  };
  context.subscriptions.push(activateTagClosing(tagProvider));

  setupCommands(client, context);

  setupProviders(client, context);


  client.onReady().then(() => {
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
    outputChannelName: "[galaxyls]",
    synchronize: {

    },
  };
}

/**
 * Returns a LanguageClient instance that will connect to a Language Server running on localhost using the given port.
 * @param port The port where the server is listening
 */
function connectToLanguageServerTCP(port: number): LanguageClient {
  const serverOptions: ServerOptions = () => {
    return new Promise((resolve, _reject) => {
      const clientSocket = new net.Socket();
      clientSocket.connect(port, "127.0.0.1", () => {
        resolve({
          reader: clientSocket,
          writer: clientSocket,
        });
      });
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
function startLanguageServer(
  command: string, args: string[], cwd: string,
): LanguageClient {
  const serverOptions: ServerOptions = {
    args,
    command,
    options: { cwd },
  };

  return new LanguageClient(command, serverOptions, getClientOptions());
}

/**
 * Defines the rules for auto-indentation.
 * From: https://github.com/redhat-developer/vscode-xml/blob/027c492f8c137682a2432a2f27046ccd260e63a3/src/extension.ts#L458
 */
function getIndentationRules(): LanguageConfiguration {
  return {
    indentationRules: {
      increaseIndentPattern: /<(?!\?|[^>]*\/>)([-_\.A-Za-z0-9]+)(?=\s|>)\b[^>]*>(?!.*<\/\1>)|<!--(?!.*-->)|\{[^}"']*$/,
      decreaseIndentPattern: /^\s*(<\/[-_\.A-Za-z0-9]+\b[^>]*>|-->|\})/
    },
    onEnterRules: [
      {
        beforeText: new RegExp(`<([_:\\w][_:\\w-.\\d]*)([^/>]*(?!/)>)[^<]*$`, 'i'),
        afterText: /^<\/([_:\w][_:\w-.\d]*)\s*>/i,
        action: { indentAction: IndentAction.IndentOutdent }
      },
      {
        beforeText: new RegExp(`<(\\w[\\w\\d]*)([^/>]*(?!/)>)[^<]*$`, 'i'),
        action: { indentAction: IndentAction.Indent }
      }
    ]
  };
}
