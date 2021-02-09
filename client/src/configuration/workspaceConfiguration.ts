import { IPlanemoConfiguration } from "../planemo/configuration";

export interface IWorkspaceConfiguration {

    planemo(): IPlanemoConfiguration;
}

export class ConfigValidationResult {
    private readonly errorMessages: string[] = []

    public isValid(): boolean {
        return this.errorMessages.length === 0;
    }

    public hasErrors(): boolean {
        return this.errorMessages.length > 0;
    }

    public addErrorMessage(errorMessage: string) {
        this.errorMessages.push(errorMessage);
    }

    public getErrorsAsString(): string {
        return this.errorMessages.join("\n");
    }
}
