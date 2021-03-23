'use strict';

import { TreeItem, TreeItemCollapsibleState, Uri } from "vscode";


export class DirectoryTreeItem extends TreeItem {

    constructor(
        public readonly label: string,
        public readonly directoryUri: Uri,
        public readonly tooltip?: string | undefined,
        public readonly collapsibleState: TreeItemCollapsibleState = TreeItemCollapsibleState.None,
    ) {
        super(label, collapsibleState);
        this.description = directoryUri.fsPath;
        this.contextValue = "directoryItem";
    }
}
