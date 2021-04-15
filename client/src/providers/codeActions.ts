import { CancellationToken, CodeAction, CodeActionContext, CodeActionKind, CodeActionProvider, Command, Diagnostic, ProviderResult, Range, Selection, TextDocument } from "vscode";
import { Commands } from "../commands";
import { DiagnosticCodes } from "../constants";


export class GalaxyToolsCodeActionProvider implements CodeActionProvider {
    public static readonly providedCodeActionKinds = [
        CodeActionKind.Empty
    ];

    provideCodeActions(document: TextDocument, range: Range | Selection, context: CodeActionContext, token: CancellationToken): ProviderResult<(CodeAction | Command)[]> {

        return context.diagnostics
            .filter(diagnostic => diagnostic.code === DiagnosticCodes.INVALID_EXPANDED_TOOL)
            .map(diagnostic => this.createPreviewExpandedDocumentCommand(diagnostic));
    }

    private createPreviewExpandedDocumentCommand(diagnostic: Diagnostic): CodeAction {
        const action = new CodeAction('Preview expanded tool document...', CodeActionKind.Empty);
        action.command = { command: Commands.PREVIEW_EXPANDED_DOCUMENT, title: 'Preview expanded tool document', tooltip: 'This will open a preview of the tool document with all the macros expanded.' };
        action.diagnostics = [diagnostic];
        action.isPreferred = true;
        return action;
    }

}
