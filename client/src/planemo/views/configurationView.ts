'use strict';

import { EOL } from 'os';
import * as path from 'path';
import { lookpath } from "lookpath"
import { Event, EventEmitter, ExtensionContext, ThemeIcon, TreeDataProvider, TreeItem, TreeItemCollapsibleState, Uri, window } from "vscode";
import { execAsync, readFile } from '../../utils';
import { IConfigurationFactory, IPlanemoConfiguration } from "../configuration";
import { DirectoryTreeItem } from '../../views/common';

const PLANEMO_LABEL = "Planemo";
const GALAXY_LABEL = "Galaxy";
const UNKNOWN = "Unknown";
const PLANEMO_BINARY = "planemo";

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
                    const versionItem = await this.getPlanemoVersionItem(planemoConfig);
                    const pathItem = await this.getPlanemoPathItem(planemoConfig);
                    const galaxyItem = await this.getPlanemoGalaxyItem(planemoConfig);

                    return [
                        versionItem,
                        pathItem,
                        galaxyItem,
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
            description: planemoVersion,
            collapsibleState: TreeItemCollapsibleState.None,
            tooltip: planemoConfig.binaryPath()
        };
        return item;
    }

    private async getPlanemoPathItem(planemoConfig: IPlanemoConfiguration): Promise<TreeItem> {
        const planemoPath = await this.getPlanemoPath(planemoConfig.binaryPath());
        const item: TreeItem = {
            label: "Path",
            description: planemoPath,
            tooltip: `Using planemo binary in: ${planemoPath}`,
            collapsibleState: TreeItemCollapsibleState.None,
        };
        return item;
    }

    private async getPlanemoPath(planemoPathInConfig: string): Promise<string> {
        try {
            if (planemoPathInConfig === PLANEMO_BINARY) {
                const valueOnPath = await lookpath(PLANEMO_BINARY);
                if (valueOnPath !== undefined) {
                    return valueOnPath;
                }
            }
            return planemoPathInConfig;
        }
        catch (err) {
            return UNKNOWN;
        }
    }

    private async getPlanemoVersion(planemoConfig: IPlanemoConfiguration): Promise<string> {
        try {
            const planemoPath = planemoConfig.binaryPath();
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
        const label = "Root";
        const galaxyRootUri = Uri.file(galaxyRootPath!);
        const tooltip = "Root of development galaxy directory to execute commands with.";
        const item = new DirectoryTreeItem(label, galaxyRootUri, tooltip);
        return item;
    }
}







