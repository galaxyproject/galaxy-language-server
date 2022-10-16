import { IPlanemoConfiguration } from "../planemo/configuration";

export namespace Settings {
    export namespace Server {
        export const SILENT_INSTALL = "galaxyTools.server.silentInstall";
    }
    export namespace Completion {
        export const MODE = "galaxyTools.completion.mode";
        export const AUTO_CLOSE_TAGS = "galaxytools.completion.autoCloseTags";
    }

    export namespace Planemo {
        export const ENABLED = "galaxyTools.planemo.enabled";
        export const ENV_PATH = "galaxyTools.planemo.envPath";
        export const GALAXY_ROOT = "galaxyTools.planemo.galaxyRoot";

        export namespace Testing {
            export const ENABLED = "galaxyTools.planemo.testing.enabled";
            export const AUTO_DISCOVERY_ON_SAVE_ENABLED = "galaxyTools.planemo.testing.autoTestDiscoverOnSaveEnabled";
            export const EXTRA_PARAMS = "galaxyTools.planemo.testing.extraParams";
        }
    }
}

export interface IServerConfiguration {
    silentInstall(): boolean;
}

export interface IWorkspaceConfiguration {
    server(): IServerConfiguration;
    planemo(): IPlanemoConfiguration;
}

export class ConfigValidationResult {
    private readonly errorMessages: string[] = [];

    constructor(private validPlanemo: boolean, private validGalaxyRoot: boolean) {}

    public isValidPlanemo(): boolean {
        return this.validPlanemo;
    }

    public isValidGalaxyRoot(): boolean {
        return this.validGalaxyRoot;
    }

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
