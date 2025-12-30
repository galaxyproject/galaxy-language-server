// Based on https://github.com/kondratyev-nv/vscode-python-test-adapter/blob/master/src/processRunner.ts

import { ChildProcess, spawn } from "child_process";
import * as iconv from "iconv-lite";
import { EOL } from "os";
import { logger } from "./logger";

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
        logger.debug(`Starting process: ${command} ${args?.join(' ') || ''}`);
        this.commandProcess = spawn(command, args, {
            cwd: configuration?.cwd,
            env: {
                ...process.env,
                ...configuration?.environment,
            },
        });
        this.pid = this.commandProcess.pid;
        this.acceptedExitCodes = configuration?.acceptedExitCodes || [0, 1];
        
        if (this.pid) {
            logger.debug(`Process started with PID: ${this.pid}`);
        } else {
            logger.warn("Process started but PID is undefined");
        }
    }

    public async complete(): Promise<{ exitCode: number; output: string }> {
        return new Promise<{ exitCode: number; output: string }>((resolve, reject) => {
            const stdoutBuffer: Buffer[] = [];
            const stderrBuffer: Buffer[] = [];
            this.commandProcess.stdout!.on("data", (chunk) => stdoutBuffer.push(chunk));
            this.commandProcess.stderr!.on("data", (chunk) => stderrBuffer.push(chunk));

            this.commandProcess.once("close", (exitCode) => {
                if (exitCode === null) {
                    logger.error("Process exit code was null");
                    reject(new Error(`Process exit code was null`));
                    return;
                }

                if (this.acceptedExitCodes.includes(exitCode)) {
                    logger.debug(`Process completed successfully with exit code: ${exitCode}`);
                    const output = decode(stdoutBuffer);
                    resolve({ exitCode, output });
                } else {
                    const error = decode(stderrBuffer);
                    logger.error(`Process failed with exit code ${exitCode}: ${error}`);
                    reject(new Error(`Process exited with code ${exitCode}: ${error}`));
                }
            });

            this.commandProcess.once("error", (error) => {
                logger.error(`Process execution error: ${error}`);
                reject(new Error(`Error occurred during process execution: ${error}`));
            });
        });
    }

    public cancel(): void {
        logger.debug(`Cancelling process with PID: ${this.pid}`);
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
