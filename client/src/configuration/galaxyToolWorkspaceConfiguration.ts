import { existsSync } from "fs";
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

    enabled(): boolean {
        return this.config.get("planemo.enabled", true);
    }
    envPath(): string {
        return this.config.get("planemo.envPath", "planemo");
    }
    galaxyRoot(): string | null {
        return this.config.get("planemo.galaxyRoot", null);
    }

    getCwd(): string | undefined {
        return workspace.workspaceFolders ? workspace.workspaceFolders[0].uri.fsPath : undefined
    }

    testing(): IPlanemoTestingConfiguration {
        return this.planemoTestingConfig;
    }

    Validate(): ConfigValidationResult {
        const result = new ConfigValidationResult();

        const envPath = this.envPath();
        if (envPath === null || !envPath.endsWith("planemo") || !existsSync(envPath)) {
            result.addErrorMessage("Please set a valid `envPath` for planemo in the configuration.")
        }

        const galaxyRoot = this.galaxyRoot();
        if (galaxyRoot === null || !galaxyRoot.endsWith("galaxy") || !existsSync(envPath)) {
            result.addErrorMessage("Please set a valid `galaxyRoot` for planemo in the configuration.")
        }

        return result;
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
