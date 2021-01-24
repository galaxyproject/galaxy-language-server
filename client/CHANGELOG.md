# Galaxy Tools (VS Code Extension) Changelog

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
