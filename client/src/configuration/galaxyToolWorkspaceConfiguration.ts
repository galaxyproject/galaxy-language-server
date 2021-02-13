import { existsSync } from "fs";

import { lookpath } from "lookpath"
import { workspace, WorkspaceConfiguration } from 'vscode';

import { IPlanemoConfiguration, IPlanemoTestingConfiguration } from "../planemo/configuration";
import { ConfigValidationResult, IWorkspaceConfiguration } from "./workspaceConfiguration";



export class GalaxyToolsWorkspaceConfiguration implements IWorkspaceConfiguration {

    private readonly config: WorkspaceConfiguration;
    private readonly planemoConfig: IPlanemoConfiguration;

    constructor() {
        this.config = workspace.getConfiguration("galaxyTools");
        this.planemoConfig = new GalaxyToolsPlanemoConfiguration(this.config);
    }

    planemo(): IPlanemoConfiguration {
        return this.planemoConfig;
    }
}

class GalaxyToolsPlanemoConfiguration implements IPlanemoConfiguration {
    private readonly planemoTestingConfig: IPlanemoTestingConfiguration;

    constructor(private readonly config: WorkspaceConfiguration) {
        this.planemoTestingConfig = new GalaxyToolsPlanemoTestingConfiguration(this.config)
    }

    public enabled(): boolean {
        return this.config.get("planemo.enabled", true);
    }
    public envPath(): string {
        return this.config.get("planemo.envPath", "planemo");
    }
    public galaxyRoot(): string | null {
        return this.config.get("planemo.galaxyRoot", null);
    }

    public getCwd(): string | undefined {
        return workspace.workspaceFolders ? workspace.workspaceFolders[0].uri.fsPath : undefined
    }

    public testing(): IPlanemoTestingConfiguration {
        return this.planemoTestingConfig;
    }

    public async validate(): Promise<ConfigValidationResult> {
        const result = new ConfigValidationResult();

        if (!this.isPlanemoInstalled()) {
            result.addErrorMessage("Please set a valid `envPath` value for planemo in the configuration.")
        }

        const galaxyRoot = this.galaxyRoot();
        if (galaxyRoot === null || !galaxyRoot.endsWith("galaxy") || !existsSync(galaxyRoot)) {
            result.addErrorMessage("Please set a valid `galaxyRoot` for planemo in the configuration.")
        }

        return result;
    }

    private async isPlanemoInstalled(): Promise<boolean> {
        try {
            const envPath = this.envPath();
            const isOnPath = await lookpath('planemo') !== undefined;
            return envPath !== null && envPath.endsWith("planemo") && (isOnPath || existsSync(envPath));
        }
        catch (err) {
            return false;
        }
    }
}

class GalaxyToolsPlanemoTestingConfiguration implements IPlanemoTestingConfiguration {

    constructor(private readonly config: WorkspaceConfiguration) { }

    enabled(): boolean {
        return this.config.get("planemo.testing.enabled", true);
    }
    autoTestDiscoverOnSaveEnabled(): boolean {
        return this.config.get("planemo.testing.autoTestDiscoverOnSaveEnabled", true);
    }
}
