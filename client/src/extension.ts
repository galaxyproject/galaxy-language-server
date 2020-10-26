"use strict";

import * as net from "net";
import { ExtensionContext, window, TextDocument, Position } from "vscode";
import { LanguageClient, LanguageClientOptions, ServerOptions } from "vscode-languageclient";
import { activateTagClosing, TagCloseRequest } from './tagClosing';
import { installLanguageServer } from './setup';
import { GALAXY_LS } from './constants';

let client: LanguageClient;

/**
 * This method gets called when the extension gets activated for the first time.
 * @param context The extension context
 */
export async function activate(context: ExtensionContext) {
  if (isDebugMode()) {
    // Development - Connect to language server (already running) using TCP
    client = connectToLanguageServerTCP(2087);
  } else {
    // Production - Install (first time only), launch and connect to language server.
    try {
      const python = await installLanguageServer(context);
      client = startLanguageServer(python, ["-m", GALAXY_LS], context.extensionPath);
    } catch (err) {
      window.showErrorMessage(err);
    }
  }

  context.subscriptions.push(client.start());

  // Setup auto close tags
  const tagProvider = (document: TextDocument, position: Position) => {
    let param = client.code2ProtocolConverter.asTextDocumentPositionParams(document, position);
    let text = client.sendRequest(TagCloseRequest.type, param);
    return text;
  };
  context.subscriptions.push(activateTagClosing(tagProvider));
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
      { scheme: "file", language: "xml" },
      { scheme: "untitled", language: "xml" },
    ],
    outputChannelName: "[galaxyls]",
    synchronize: {

    },
  };
}

function isDebugMode(): boolean {
  return process.env.VSCODE_DEBUG_MODE === "true";
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
