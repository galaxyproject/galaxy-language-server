import { Range, TestItem, Uri } from "vscode";

export const CRLF = "\r\n";

export type TestState = "running" | "passed" | "failed" | "skipped" | "errored";

export type ToolTestData = ToolTestSuite | ToolTestCase;

export const testDataMap = new WeakMap<TestItem, ToolTestData>();

/**
 * Information about a test suite for a particular tool.
 */
export class ToolTestSuite {
    constructor(
        public readonly id: string,
        public readonly label: string,
        public readonly uri: Uri,
        public readonly range: Range,
        public readonly children: Array<ToolTestCase>
    ) {}
}

/**
 * Information about a test case.
 */
export class ToolTestCase {
    constructor(
        public readonly id: string,
        public readonly label: string,
        public readonly uri: Uri,
        public readonly range: Range
    ) {}
}

export interface IToolTestSuite {
    id: string;
    label: string;
    uri: string;
    range: Range;
    children: Array<IToolTestCase>;
}

export interface IToolTestCase {
    id: string;
    label: string;
    uri: string;
    range: Range;
}
