// Based on https://github.com/kondratyev-nv/vscode-python-test-adapter/blob/master/src/processRunner.ts

import { ChildProcess, spawn } from "child_process";
import * as iconv from "iconv-lite";
import { EOL } from "os";

export interface IProcessRunConfiguration {
    cwd?: string;
    environment?: { [key: string]: string | undefined };
    acceptedExitCodes?: readonly number[];
}

export interface IProcessExecution {
    pid: number | undefined;

    complete(): Promise<{ exitCode: number; output: string }>;

    cancel(): void;
}

class CommandProcessExecution implements IProcessExecution {
    public readonly pid: number | undefined;

    private readonly commandProcess: ChildProcess;
    private readonly acceptedExitCodes: readonly number[];

    constructor(command: string, args?: string[], configuration?: IProcessRunConfiguration) {
        this.commandProcess = spawn(command, args, {
            cwd: configuration?.cwd,
            env: {
                ...process.env,
                ...configuration?.environment,
            },
        });
        this.pid = this.commandProcess.pid;
        this.acceptedExitCodes = configuration?.acceptedExitCodes || [0, 1];
    }

    public async complete(): Promise<{ exitCode: number; output: string }> {
        return new Promise<{ exitCode: number; output: string }>((resolve, reject) => {
            const stdoutBuffer: Buffer[] = [];
            const stderrBuffer: Buffer[] = [];
            this.commandProcess.stdout!.on("data", (chunk) => stdoutBuffer.push(chunk));
            this.commandProcess.stderr!.on("data", (chunk) => stderrBuffer.push(chunk));

            this.commandProcess.once("close", (exitCode) => {
                if (exitCode === null) {
                    reject(new Error(`Process exit code was null`));
                    return;
                }

                if (this.acceptedExitCodes.indexOf(exitCode) < 0 && !this.commandProcess.killed) {
                    const error = decode(stderrBuffer);
                    reject(new Error(`Process exited with code ${exitCode}: ${error}`));
                    return;
                }

                const output = decode(stdoutBuffer);
                if (!output) {
                    if (stdoutBuffer.length > 0) {
                        reject(new Error("Can not decode output from the process"));
                    } else if (stderrBuffer.length > 0 && !this.commandProcess.killed) {
                        reject(new Error(`Process returned an error:${EOL}${decode(stderrBuffer)}`));
                    }
                }
                resolve({ exitCode, output });
            });

            this.commandProcess.once("error", (error) => {
                reject(new Error(`Error occurred during process execution: ${error}`));
            });
        });
    }
    public cancel(): void {
        this.commandProcess.kill("SIGINT");
    }
}

export function runProcess(
    command: string,
    args?: string[],
    configuration?: IProcessRunConfiguration
): IProcessExecution {
    return new CommandProcessExecution(command, args, configuration);
}

function decode(buffers: Buffer[]) {
    return iconv.decode(Buffer.concat(buffers), "utf8");
}
