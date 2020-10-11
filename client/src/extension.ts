"use strict";

import * as net from "net";
import { ExtensionContext, window, TextDocument, Position } from "vscode";
import { LanguageClient, LanguageClientOptions, ServerOptions } from "vscode-languageclient";
import { activateTagClosing, TagCloseRequest } from './tagClosing';
import { installLSWithProgress } from './setup';
import { GALAXY_LS } from './constants';

let client: LanguageClient;

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

function isStartedInDebugMode(): boolean {
  return process.env.VSCODE_DEBUG_MODE === "true";
}

function startLangServerTCP(port: number): LanguageClient {
  const serverOptions: ServerOptions = () => {
    return new Promise((resolve, reject) => {
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

function startLangServer(
  command: string, args: string[], cwd: string,
): LanguageClient {
  const serverOptions: ServerOptions = {
    args,
    command,
    options: { cwd },
  };

  return new LanguageClient(command, serverOptions, getClientOptions());
}

export async function activate(context: ExtensionContext) {
  if (isStartedInDebugMode()) {
    // Development - Run the server manually
    client = startLangServerTCP(2087);
  } else {
    // Production - Client is going to run the server (for use within `.vsix` package)
    try {
      const python = await installLSWithProgress(context);
      client = startLangServer(python, ["-m", GALAXY_LS], context.extensionPath);
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

export function deactivate(): Thenable<void> {
  return client ? client.stop() : Promise.resolve();
}
