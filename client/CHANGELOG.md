# Galaxy Tools (VS Code Extension) Changelog

## [0.7.3] - 2022-09-06

### Fixed

- Bug in Python version parsing ([#200](https://github.com/galaxyproject/galaxy-language-server/pull/200)).

## [0.7.2] - 2022-08-14

### Fixed

- Remove local virtual environment when install fails ([#196](https://github.com/galaxyproject/galaxy-language-server/pull/196)).

## [0.7.1] - 2022-01-31

### Fixed

-   Error when trying to discover tests in non-Galaxy tool documents ([#189](https://github.com/galaxyproject/galaxy-language-server/pull/189)).

### Changed

-   Updated Galaxy Language Server [v0.7.1](./server/CHANGELOG.md#071)

## [0.7.0] - 2022-01-29

### Changed

-   Updated Galaxy Language Server [v0.7.0](./server/CHANGELOG.md#070)

-   Adapt how custom external (server) and internal commands are handled ([#179](https://github.com/galaxyproject/galaxy-language-server/pull/179)).

-   Migrate to native VSCode Testing API and drop dependency on `Test Explorer UI extension` (you can now safely uninstall this extension if no other extensions depends on it) ([#183](https://github.com/galaxyproject/galaxy-language-server/pull/183)).

## [0.6.1] - 2021-09-26

### Changed

-   Updated Galaxy Language Server [v0.6.1](./server/CHANGELOG.md#061)

## [0.6.0] - 2021-09-12

### Changed

-   The settings contains now an `extraParams` value to customize and pass extra parameters to `planemo` when running tests inside the IDE ([#164](https://github.com/galaxyproject/galaxy-language-server/pull/164)).

-   Updated Galaxy Language Server [v0.6.0](./server/CHANGELOG.md#060)

## [0.5.3] - 2021-07-09

### Fixed

-   The `galaxy_root` setting validation now checks for the existence of `<galaxy_root>/lib/galaxy` instead of relying on how the root directory is named. ([#158](https://github.com/galaxyproject/galaxy-language-server/pull/158)).

### Changed

-   Updated Galaxy Language Server [v0.5.3](./server/CHANGELOG.md#053)

## [0.5.2] - 2021-06-08

### Fixed

-   Duplicated CodeActions for the same expand document command ([#152](https://github.com/galaxyproject/galaxy-language-server/pull/152)).

-   The expanded document preview was not updating with the source document changes ([#148](https://github.com/galaxyproject/galaxy-language-server/pull/148)).

### Changed

-   Updated Galaxy Language Server [v0.5.2](./server/CHANGELOG.md#052)

## [0.5.1] - 2021-06-03

### Changed

-   Updated Galaxy Language Server [v0.5.1](./server/CHANGELOG.md#051)

-   Updated development dependencies ([#142](https://github.com/galaxyproject/galaxy-language-server/pull/142)).

-   Include new installation troubleshooting entry in the readme for `pip module not found` error ([#141](https://github.com/galaxyproject/galaxy-language-server/pull/141)).

## [0.5.0] - 2021-05-13

### Added

-   New Planemo Explorer configuration view ([#125](https://github.com/galaxyproject/galaxy-language-server/pull/125)).

-   Command to generate the expanded version of a tool document ([#128](https://github.com/galaxyproject/galaxy-language-server/pull/128)).

### Changed

-   Improved error diagnostics when validating a tool with problems in the referenced macro files ([#128](https://github.com/galaxyproject/galaxy-language-server/pull/128)).

-   All dependencies were updated, including `vscode-languageclient` to version `7.0.0` which required some changes ([#130](https://github.com/galaxyproject/galaxy-language-server/pull/130)).

-   Updated Galaxy Language Server [v0.5.0](./server/CHANGELOG.md#050)

## [0.4.1] - 2021-02-27

### Added

-   After running the tests from the Test Explorer a link to the full HTML test report will appear in the output console ([#122](https://github.com/galaxyproject/galaxy-language-server/pull/122)).

### Changed

-   Various improvements in the installation process. Lightweight extension bundle, remember selected Python binary on updates, and less repeated notifications ([#120](https://github.com/galaxyproject/galaxy-language-server/pull/120)).
-   Detach client and server versions. Now both versions can evolve independently ([#119](https://github.com/galaxyproject/galaxy-language-server/pull/119)).
-   Hide command and view contributions when the extension is not active. This will make the commands and the planemo explorer icon visible only if the extension is active and not all the time ([#117](https://github.com/galaxyproject/galaxy-language-server/pull/117)).

## [0.4.0] - 2021-02-15

### Added

-   New settings to integrate [planemo](https://github.com/galaxyproject/planemo) and run `planemo test` inside [Test Explorer UI](https://marketplace.visualstudio.com/items?itemName=hbenl.vscode-test-explorer) for the currently opened tool documents ([#110](https://github.com/galaxyproject/galaxy-language-server/pull/110)).

-   Commands to reorder `<param>` attributes (in a single tag `Ctrl+Alt+s Ctrl+Alt+p` or the whole document `Ctrl+Alt+s Ctrl+Alt+d`) according to the IUC Style Guidelines ([#104](https://github.com/galaxyproject/galaxy-language-server/pull/104)).

### Fixed

-   Display error notification when a code generation command fails ([#113](https://github.com/galaxyproject/galaxy-language-server/pull/113)).

### Changed

-   Update gx-tool snippet to latests IUC best practices ([#94](https://github.com/galaxyproject/galaxy-language-server/pull/94)).
-   Updated Galaxy Language Server [v0.4.0](./server/CHANGELOG.md#040)

## [0.3.2] - 2021-01-24

### Changed

-   Minor improvements in snippets ([#101](https://github.com/galaxyproject/galaxy-language-server/pull/101)).
-   Updated Galaxy Language Server [v0.3.2](./server/CHANGELOG.md#032)

## [0.3.1] - 2021-01-09

### Added

-   New snippet for bio.tools `xrefs` ([#87](https://github.com/galaxyproject/galaxy-language-server/pull/87/files)).

### Changed

-   Updated Galaxy Language Server [v0.3.1](./server/CHANGELOG.md#031)

## [0.3.0] - 2021-01-01

### Added

-   Custom language definition (XML dialect) for Galaxy Tool Wrapper files and basic embedded language syntax highlighting (`Cheetah` and `reStructuredText`) ([#79](https://github.com/galaxyproject/galaxy-language-server/pull/79)).
-   A custom command (`Ctrl+Alt+c`) to auto-generate the `<command>` section with boilerplate Cheetah template based on the current `inputs` and `outputs` defined in the tool ([#77](https://github.com/galaxyproject/galaxy-language-server/pull/77)).
-   A custom command (`Ctrl+Alt+t`) to auto-generate `<test>` cases based on the current `inputs` and `outputs` defined in the tool ([#73](https://github.com/galaxyproject/galaxy-language-server/pull/73)).
-   New snippets for common `param` definitions ([#71](https://github.com/galaxyproject/galaxy-language-server/pull/71/files)).

### Changed

-   Updated Galaxy Language Server [v0.3.0](./server/CHANGELOG.md#030)

## [0.2.1] - 2020-11-22

### Changed

-   The installation process of the language server now provides more feedback to the user ([#65](https://github.com/galaxyproject/galaxy-language-server/pull/65)).
-   Updated Galaxy Language Server [v0.2.1](./server/CHANGELOG.md#021)

## [0.2.0] - 2020-11-13

### Added

-   Settings to control completion features ([#56](https://github.com/galaxyproject/galaxy-language-server/pull/56)).
-   Auto indent on new line ([#52](https://github.com/galaxyproject/galaxy-language-server/pull/52))

### Changed

-   Updated Galaxy Language Server [v0.2.0](./server/CHANGELOG.md#020)

## [0.1.2] - 2020-10-25

### Changed

-   Updated Galaxy Language Server [v0.1.2](./server/CHANGELOG.md#012)
-   Change icon background to dark.

### Fixed

-   Fix error preventing the language server to start or install in Unix systems ([#49](https://github.com/galaxyproject/galaxy-language-server/pull/49)).

## [0.1.1] - 2020-10-24 [YANKED]

### Changed

-   Updated Galaxy Language Server [v0.1.1](./server/CHANGELOG.md#011).
-   Improved language server installation.
-   Updated some dependencies.

## [0.1.0] - 2020-10-14

### Added

-   Support for Galaxy Language Server [v0.1.0](./server/CHANGELOG.md#010).
-   Auto-installation of language server in the extension's virtual environment.
-   [Snippets](./client/src/snippets.json) for basic tool scaffolding.
