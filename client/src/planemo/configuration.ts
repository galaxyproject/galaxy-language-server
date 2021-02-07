import { GalaxyToolsWorkspaceConfiguration } from "../configuration/galaxyToolWorkspaceConfiguration";
import { IWorkspaceConfiguration } from "../configuration/workspaceConfiguration";

export interface IPlanemoConfiguration {

    enabled(): boolean;

    envPath(): string | null;

    galaxyPath(): string | null;

    testingEnabled(): boolean;

    autoTestDiscoverOnSaveEnabled(): boolean;
}

export interface IConfigurationFactory {
    getConfiguration(): IWorkspaceConfiguration;
}

export class DefaultConfigurationFactory implements IConfigurationFactory {
    constructor() { }

    public getConfiguration(): IWorkspaceConfiguration {
        return new GalaxyToolsWorkspaceConfiguration();
    }
}
