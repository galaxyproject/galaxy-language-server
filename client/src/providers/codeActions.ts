import {
    CancellationToken,
    CodeAction,
    CodeActionContext,
    CodeActionKind,
    CodeActionProvider,
    Command,
    Diagnostic,
    ProviderResult,
    Range,
    Selection,
    TextDocument,
} from "vscode";
import { Commands } from "../commands";
import { DiagnosticCodes } from "../constants";

export class GalaxyToolsCodeActionProvider implements CodeActionProvider {
    public static readonly providedCodeActionKinds = [CodeActionKind.Empty];

    provideCodeActions(
        document: TextDocument,
        range: Range | Selection,
        context: CodeActionContext,
        token: CancellationToken
    ): ProviderResult<(CodeAction | Command)[]> {
        const resultCodeActions: CodeAction[] = [];

        const expanded_tool_diagnostics = context.diagnostics.filter(
            (diagnostic) => diagnostic.code === DiagnosticCodes.INVALID_EXPANDED_TOOL
        );
        if (expanded_tool_diagnostics.length) {
            resultCodeActions.push(this.createPreviewExpandedDocumentCommand(expanded_tool_diagnostics));
        }

        return resultCodeActions;
    }

    private createPreviewExpandedDocumentCommand(diagnostics: Diagnostic[]): CodeAction {
        const action = new CodeAction("Preview expanded tool document...", CodeActionKind.Empty);
        action.command = {
            command: Commands.PREVIEW_EXPANDED_DOCUMENT.internal,
            title: "Preview expanded tool document",
            tooltip: "This will open a preview of the tool document with all the macros expanded.",
        };
        action.diagnostics = diagnostics;
        action.isPreferred = true;
        return action;
    }
}
