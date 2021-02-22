'use strict';

import { Memento } from "vscode";

const PYTHON_STORED_PATH = "galaxytools.python.stored.path";
const SERVER_INSTALLED = "galaxytools.server.installed";

export class LocalStorageService {

    constructor(private storage: Memento) { }

    public getStoredPython(): string | null {
        const result = this.getValue<string>(PYTHON_STORED_PATH);
        return result;
    }

    public setStoredPython(pythonPath: string) {
        this.setValue<string>(PYTHON_STORED_PATH, pythonPath);
    }

    public clearStoredPython() {
        this.setValue<string>(PYTHON_STORED_PATH, null);
    }

    public isServerFirstTimeInstall(): boolean {
        const isServerInstalled = this.getValue<boolean>(SERVER_INSTALLED);
        return isServerInstalled !== true;
    }

    public setServerInstalled() {
        this.setValue<boolean>(SERVER_INSTALLED, true);
    }

    public getValue<T>(key: string): T | null {
        return this.storage.get<T | null>(key, null);
    }

    public setValue<T>(key: string, value: T | null) {
        this.storage.update(key, value);
    }
}
