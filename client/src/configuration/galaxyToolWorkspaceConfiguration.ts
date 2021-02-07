import { workspace, WorkspaceConfiguration } from 'vscode';

import { IPlanemoConfiguration } from "../planemo/configuration";
import { IWorkspaceConfiguration } from "./workspaceConfiguration";



export class GalaxyToolsWorkspaceConfiguration implements IWorkspaceConfiguration {

    private readonly config: WorkspaceConfiguration;
    private readonly planemoConfig: IPlanemoConfiguration;

    constructor() {
        this.config = workspace.getConfiguration("galaxyTools");
        this.planemoConfig = new GalaxyToolsPlanemoConfiguration(this.config);
    }


    getPlanemoConfiguration(): IPlanemoConfiguration {
        return this.planemoConfig;
    }
}

class GalaxyToolsPlanemoConfiguration implements IPlanemoConfiguration {

    constructor(private readonly config: WorkspaceConfiguration) {
    }

    enabled(): boolean {
        return this.config.get("planemo.enabled", true);
    }
    envPath(): string | null {
        return this.config.get("planemo.envPath", null);
    }
    galaxyPath(): string | null {
        return this.config.get("planemo.galaxyPath", null);
    }
    testingEnabled(): boolean {
        return this.config.get("planemo.testing.enabled", true);
    }
    autoTestDiscoverOnSaveEnabled(): boolean {
        return this.config.get("planemo.testing.autoTestDiscoverOnSaveEnabled", true);
    }
}
