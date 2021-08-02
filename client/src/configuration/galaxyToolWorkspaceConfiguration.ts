import { join } from "path";
import { lookpath } from "lookpath";
import { workspace, WorkspaceConfiguration } from "vscode";

import { IPlanemoConfiguration, IPlanemoTestingConfiguration } from "../planemo/configuration";
import { exists } from "../utils";
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
        this.planemoTestingConfig = new GalaxyToolsPlanemoTestingConfiguration(this.config);
    }

    public enabled(): boolean {
        return this.config.get("planemo.enabled", true);
    }
    public binaryPath(): string {
        return this.config.get("planemo.envPath", "planemo");
    }
    public galaxyRoot(): string | null {
        return this.config.get("planemo.galaxyRoot", null);
    }

    public getCwd(): string | undefined {
        return workspace.workspaceFolders ? workspace.workspaceFolders[0].uri.fsPath : undefined;
    }

    public testing(): IPlanemoTestingConfiguration {
        return this.planemoTestingConfig;
    }

    public async validate(): Promise<ConfigValidationResult> {
        const validPlanemo = await this.isPlanemoInstalled();
        const validGalaxyRoot = await this.isValidGalaxyRoot();

        const result = new ConfigValidationResult(validPlanemo, validGalaxyRoot);

        if (!validPlanemo) {
            result.addErrorMessage("Please set a valid `envPath` value for planemo in the configuration.");
        }

        if (!validGalaxyRoot) {
            result.addErrorMessage("Please set a valid `galaxyRoot` for planemo in the configuration.");
        }

        return result;
    }

    private async isValidGalaxyRoot(): Promise<boolean> {
        const galaxyRoot = this.galaxyRoot();
        if (galaxyRoot === null || !(await exists(join(galaxyRoot, "lib", "galaxy")))) {
            return false;
        }
        return true;
    }

    private async isPlanemoInstalled(): Promise<boolean> {
        try {
            const envPath = this.binaryPath();
            const isOnPath = (await lookpath("planemo")) !== undefined;
            return envPath !== null && envPath.endsWith("planemo") && (isOnPath || (await exists(envPath)));
        } catch (err) {
            return false;
        }
    }
}

class GalaxyToolsPlanemoTestingConfiguration implements IPlanemoTestingConfiguration {
    constructor(private readonly config: WorkspaceConfiguration) {}

    enabled(): boolean {
        return this.config.get("planemo.testing.enabled", true);
    }
    autoTestDiscoverOnSaveEnabled(): boolean {
        return this.config.get("planemo.testing.autoTestDiscoverOnSaveEnabled", true);
    }
}
