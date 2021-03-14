'use strict';

import { EOL } from 'os';
import * as path from 'path';
import { Event, EventEmitter, ExtensionContext, ThemeIcon, TreeDataProvider, TreeItem, TreeItemCollapsibleState, window } from "vscode";
import { execAsync, readFile } from '../../utils';
import { IConfigurationFactory, IPlanemoConfiguration } from "../configuration";

const PLANEMO_LABEL = "Planemo";
const GALAXY_LABEL = "Galaxy";
const UNKNOWN = "Unknown";

export function registerConfigTreeDataProvider(context: ExtensionContext, configFactory: IConfigurationFactory): PlanemoConfigTreeDataProvider {

    const treeDataProvider = new PlanemoConfigTreeDataProvider(configFactory);
    const treeView = window.createTreeView("planemo-config", {
        showCollapseAll: true,
        treeDataProvider,
        canSelectMany: false,
    });
    context.subscriptions.push(treeView);
    return treeDataProvider;
}

export class PlanemoConfigTreeItem extends TreeItem {

    constructor(
        public readonly label: string,
        public readonly collapsibleState: TreeItemCollapsibleState = TreeItemCollapsibleState.Collapsed,
        public getItemChildren?: (planemoConfig: IPlanemoConfiguration) => Promise<TreeItem[]>,
    ) {
        super(label, collapsibleState);
    }

}


export class PlanemoConfigTreeDataProvider implements TreeDataProvider<TreeItem>{

    private _onDidChangeTreeData: EventEmitter<TreeItem | undefined | void> = new EventEmitter<TreeItem | undefined | void>();
    readonly onDidChangeTreeData: Event<TreeItem | undefined | void> = this._onDidChangeTreeData.event;

    constructor(private configFactory: IConfigurationFactory) {
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: TreeItem): TreeItem {
        return element;
    }

    async getChildren(element?: PlanemoConfigTreeItem): Promise<TreeItem[]> {

        const planemoConfig = this.configFactory.getConfiguration().planemo();
        const planemoConfigValidation = await planemoConfig.validate();
        if (!planemoConfigValidation.isValidPlanemo()) {
            return Promise.resolve([]);
        }

        if (element && element.getItemChildren) {
            return Promise.resolve(await element.getItemChildren(planemoConfig));
        } else {
            const rootItem: PlanemoConfigTreeItem = {
                label: PLANEMO_LABEL,
                collapsibleState: TreeItemCollapsibleState.Expanded,
                description: 'configuration details',
                contextValue: 'planemoConfigItem',
                iconPath: {
                    light: path.join(__filename, '..', '..', 'resources', 'light', 'planemo.svg'),
                    dark: path.join(__filename, '..', '..', 'resources', 'dark', 'planemo.svg')
                },
                getItemChildren: async planemoConfig => {
                    const version = await this.getPlanemoVersionItem(planemoConfig);
                    const galaxy = await this.getPlanemoGalaxyItem(planemoConfig);

                    return [
                        version,
                        galaxy,
                    ]
                }
            };
            return Promise.resolve([rootItem]);
        }

    }

    private async getPlanemoVersionItem(planemoConfig: IPlanemoConfiguration): Promise<TreeItem> {
        const planemoVersion = await this.getPlanemoVersion(planemoConfig);
        const item: TreeItem = {
            label: "Version",
            collapsibleState: TreeItemCollapsibleState.None,
            description: planemoVersion,
            tooltip: planemoConfig.envPath()
        };
        return item;
    }

    private async getPlanemoVersion(planemoConfig: IPlanemoConfiguration): Promise<string> {
        try {
            const planemoPath = planemoConfig.envPath();
            const getPlanemoVersionCmd = `"${planemoPath}" --version`;
            const commandResult = await execAsync(getPlanemoVersionCmd);
            const versionMatch = commandResult.match(new RegExp(/[\d.]+/g));
            const version = versionMatch?.pop();
            return version ?? UNKNOWN;
        } catch (error) {
            console.error(`[gls.planemo] getPlanemoVersion: ${error}`);
            return UNKNOWN;
        }
    }

    private async getPlanemoGalaxyItem(planemoConfig: IPlanemoConfiguration): Promise<PlanemoConfigTreeItem> {
        const item: PlanemoConfigTreeItem = {
            label: GALAXY_LABEL,
            description: "instance used by Planemo",
            collapsibleState: TreeItemCollapsibleState.Collapsed,
            contextValue: 'galaxyConfigItem',
            getItemChildren: async planemoConfig => {
                const children = new Array<TreeItem>();
                const version = await this.getGalaxyVersionItem(planemoConfig);
                children.push(version);

                if (version.description !== UNKNOWN) {
                    const galaxyRoot = this.getGalaxyRootItem(planemoConfig);
                    children.push(galaxyRoot);
                }

                return children;
            }
        };
        return item;
    }

    private async getGalaxyVersionItem(planemoConfig: IPlanemoConfiguration): Promise<TreeItem> {
        const version = await this.getGalaxyVersion(planemoConfig);
        const icon = new ThemeIcon(version === UNKNOWN ? "alert" : "pass");
        const item: TreeItem = {
            label: "Version",
            collapsibleState: TreeItemCollapsibleState.None,
            description: version,
            tooltip: `Galaxy ${version}`,
            iconPath: icon,
        };
        return item;
    }

    private async getGalaxyVersion(planemoConfig: IPlanemoConfiguration): Promise<string> {
        try {
            const galaxyRootPath = planemoConfig.galaxyRoot();
            const versionFilePath = path.join(galaxyRootPath!, 'lib', 'galaxy', 'version.py');
            const content = await readFile(versionFilePath);
            const lines = content.split(EOL);
            let version = undefined;
            if (lines.length > 0) {
                const versionMatch = lines[0].match(new RegExp(/VERSION_MAJOR = "(?<version>[\d.]+)"/));
                version = versionMatch?.groups?.version;
            }
            return version ?? UNKNOWN;
        } catch (error) {
            console.error(`[gls.planemo] getGalaxyVersion: ${error}`);
            return UNKNOWN;
        }
    }

    private getGalaxyRootItem(planemoConfig: IPlanemoConfiguration): TreeItem {
        const galaxyRootPath = planemoConfig.galaxyRoot();
        const galaxyRoot: TreeItem = {
            label: "Root",
            description: galaxyRootPath!,
            tooltip: "Root of development galaxy directory to execute commands with.",
            collapsibleState: TreeItemCollapsibleState.None,
        };
        return galaxyRoot;
    }
}







