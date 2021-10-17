/**
 * Represents a command that can be executed in the server or client.
 *
 * @interface ICommand
 * @member {string} external is used to execute command on Language Server
 * @member {string} internal is used to execute command on Client extension
 */
export interface ICommand {
    external: string;
    internal: string;
}
