import { exec } from "child_process";

export async function execAsync(command: string, options: object = {}): Promise<string> {
    return new Promise((resolve, reject) => {
        exec(command, options, (error, stdout, _) => {
            if (error) {
                return reject(error);
            }
            resolve(stdout.trim().toString());
        });
    });
}