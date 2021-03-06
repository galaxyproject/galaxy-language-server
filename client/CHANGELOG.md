# Galaxy Tools (VS Code Extension) Changelog

## [0.4.1] - 2021-02-27

### Added

- After running the tests from the Test Explorer a link to the full HTML test report will appear in the output console ([#122](https://github.com/galaxyproject/galaxy-language-server/pull/122)).

### Changed

- Various improvements in the installation process. Lightweight extension bundle, remember selected Python binary on updates, and less repeated notifications ([#120](https://github.com/galaxyproject/galaxy-language-server/pull/120)).
- Detach client and server versions. Now both versions can evolve independently ([#119](https://github.com/galaxyproject/galaxy-language-server/pull/119)).
- Hide command and view contributions when the extension is not active. This will make the commands and the planemo explorer icon visible only if the extension is active and not all the time ([#117](https://github.com/galaxyproject/galaxy-language-server/pull/117)).

## [0.4.0] - 2021-02-15

### Added

- New settings to integrate [planemo](https://github.com/galaxyproject/planemo) and run `planemo test` inside [Test Explorer UI](https://marketplace.visualstudio.com/items?itemName=hbenl.vscode-test-explorer) for the currently opened tool documents ([#110](https://github.com/galaxyproject/galaxy-language-server/pull/110)).

- Commands to reorder `<param>` attributes (in a single tag `Ctrl+Alt+s Ctrl+Alt+p` or the whole document `Ctrl+Alt+s Ctrl+Alt+d`) according to the IUC Style Guidelines ([#104](https://github.com/galaxyproject/galaxy-language-server/pull/104)).

### Fixed

- Display error notification when a code generation command fails ([#113](https://github.com/galaxyproject/galaxy-language-server/pull/113)).

### Changed

- Update gx-tool snippet to latests IUC best practices ([#94](https://github.com/galaxyproject/galaxy-language-server/pull/94)).
- Updated Galaxy Language Server [v0.4.0](./server/CHANGELOG.md#040)

## [0.3.2] - 2021-01-24

### Changed

- Minor improvements in snippets ([#101](https://github.com/galaxyproject/galaxy-language-server/pull/101)).
- Updated Galaxy Language Server [v0.3.2](./server/CHANGELOG.md#032)

## [0.3.1] - 2021-01-09

### Added

- New snippet for bio.tools `xrefs` ([#87](https://github.com/galaxyproject/galaxy-language-server/pull/87/files)).

### Changed

- Updated Galaxy Language Server [v0.3.1](./server/CHANGELOG.md#031)

## [0.3.0] - 2021-01-01

### Added

- Custom language definition (XML dialect) for Galaxy Tool Wrapper files and basic embedded language syntax highlighting (`Cheetah` and `reStructuredText`) ([#79](https://github.com/galaxyproject/galaxy-language-server/pull/79)).
- A custom command (`Ctrl+Alt+c`) to auto-generate the `<command>` section with boilerplate Cheetah template based on the current `inputs` and `outputs` defined in the tool ([#77](https://github.com/galaxyproject/galaxy-language-server/pull/77)).
- A custom command (`Ctrl+Alt+t`) to auto-generate `<test>` cases based on the current `inputs` and `outputs` defined in the tool ([#73](https://github.com/galaxyproject/galaxy-language-server/pull/73)).
- New snippets for common `param` definitions ([#71](https://github.com/galaxyproject/galaxy-language-server/pull/71/files)).

### Changed

- Updated Galaxy Language Server [v0.3.0](./server/CHANGELOG.md#030)

## [0.2.1] - 2020-11-22

### Changed

- The installation process of the language server now provides more feedback to the user ([#65](https://github.com/galaxyproject/galaxy-language-server/pull/65)).
- Updated Galaxy Language Server [v0.2.1](./server/CHANGELOG.md#021)

## [0.2.0] - 2020-11-13

### Added

- Settings to control completion features ([#56](https://github.com/galaxyproject/galaxy-language-server/pull/56)).
- Auto indent on new line ([#52](https://github.com/galaxyproject/galaxy-language-server/pull/52))

### Changed

- Updated Galaxy Language Server [v0.2.0](./server/CHANGELOG.md#020)

## [0.1.2] - 2020-10-25

### Changed

- Updated Galaxy Language Server [v0.1.2](./server/CHANGELOG.md#012)
- Change icon background to dark.

### Fixed

- Fix error preventing the language server to start or install in Unix systems ([#49](https://github.com/galaxyproject/galaxy-language-server/pull/49)).

## [0.1.1] - 2020-10-24 [YANKED]

### Changed

- Updated Galaxy Language Server [v0.1.1](./server/CHANGELOG.md#011).
- Improved language server installation.
- Updated some dependencies.


## [0.1.0] - 2020-10-14

### Added

- Support for Galaxy Language Server [v0.1.0](./server/CHANGELOG.md#010).
- Auto-installation of language server in the extension's virtual environment.
- [Snippets](./client/src/snippets.json) for basic tool scaffolding.
