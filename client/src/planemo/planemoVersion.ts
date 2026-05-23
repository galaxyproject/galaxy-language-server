import { gte, valid } from "semver";
import { logger } from "../logger";
import { execAsync } from "../utils";

export const UNKNOWN_PLANEMO_VERSION = "0.0.0";

const PLANEMO_TOKEN_REGEX = /\bplanemo\b/i;
const VERSION_TOKEN_REGEX = /\bversion\b/i;
const SEMVER_TOKEN_REGEX = /[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?/g;
const VERSION_WITH_PREFIX_REGEX = /\bversion\b[^\d]*([0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?)/i;

export async function getPlanemoVersion(binaryPath: string): Promise<string> {
    try {
        const getPlanemoVersionCmd = `"${binaryPath}" --version`;
        const commandResult = await execAsync(getPlanemoVersionCmd);
        const version = extractPlanemoVersion(commandResult);
        return version && valid(version) ? version : UNKNOWN_PLANEMO_VERSION;
    } catch (error) {
        logger.warn(`Failed to get Planemo version from ${binaryPath}: ${error}`);
        return UNKNOWN_PLANEMO_VERSION;
    }
}

export function isKnownPlanemoVersion(version: string): boolean {
    return version !== UNKNOWN_PLANEMO_VERSION;
}

function extractPlanemoVersion(output: string): string | undefined {
    const lines = output
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => line.length > 0);

    // Preferred path: parse a line that explicitly contains "planemo" and "version".
    for (const line of [...lines].reverse()) {
        if (!PLANEMO_TOKEN_REGEX.test(line) || !VERSION_TOKEN_REGEX.test(line)) {
            continue;
        }
        const versionMatch = line.match(VERSION_WITH_PREFIX_REGEX);
        if (versionMatch?.[1]) {
            return versionMatch[1];
        }
    }

    // Fallback: choose the last semver-looking token from output.
    const semverCandidates = output.match(SEMVER_TOKEN_REGEX);
    return semverCandidates?.pop();
}

export function meetsMinVersion(version: string, minVersion: string): boolean {
    if (!valid(version) || !valid(minVersion)) {
        return false;
    }
    return gte(version, minVersion);
}
