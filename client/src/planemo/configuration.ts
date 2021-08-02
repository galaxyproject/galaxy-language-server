import { GalaxyToolsWorkspaceConfiguration } from "../configuration/galaxyToolWorkspaceConfiguration";
import { ConfigValidationResult, IWorkspaceConfiguration } from "../configuration/workspaceConfiguration";

export interface IPlanemoConfiguration {
    enabled(): boolean;

    binaryPath(): string;

    galaxyRoot(): string | null;

    getCwd(): string | undefined;

    testing(): IPlanemoTestingConfiguration;

    validate(): Promise<ConfigValidationResult>;
}

export interface IPlanemoTestingConfiguration {
    enabled(): boolean;

    autoTestDiscoverOnSaveEnabled(): boolean;
}

export interface IConfigurationFactory {
    getConfiguration(): IWorkspaceConfiguration;
}

export class DefaultConfigurationFactory implements IConfigurationFactory {
    constructor() {}

    public getConfiguration(): IWorkspaceConfiguration {
        return new GalaxyToolsWorkspaceConfiguration();
    }
}
