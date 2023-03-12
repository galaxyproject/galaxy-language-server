# Galaxy Language Server Changelog

## [0.10.2] - 2023-03-12

### Fixed

- Fix parameters and models conversion between client and server ([#224](https://github.com/galaxyproject/galaxy-language-server/pull/224)).

## [0.10.1] - 2023-03-04

### Fixed

- Config loading issue resulting in unhandled exception with new configuration models ([#220](https://github.com/galaxyproject/galaxy-language-server/pull/220)).

## [0.10.0] - 2023-02-25

### Changed

- Update pygls to version 1.0.1. This enables Python 3.11 support and other features ([#216](https://github.com/galaxyproject/galaxy-language-server/pull/216)).

## [0.9.0] - 2022-10-20

### Added

- New setting to silently install the language server ([#210](https://github.com/galaxyproject/galaxy-language-server/pull/210)).

### Changed

- Code quality: fix e2e tests for linting ([#211](https://github.com/galaxyproject/galaxy-language-server/pull/211)).

## [0.8.0] - 2022-10-02

### Added

- Full Galaxy tool linting integration ([#204](https://github.com/galaxyproject/galaxy-language-server/pull/204)).

### Changed

- Code quality: refactor validation system ([#205](https://github.com/galaxyproject/galaxy-language-server/pull/205)).

- Code quality: setup isort ([#203](https://github.com/galaxyproject/galaxy-language-server/pull/203)).

## [0.7.1] - 2022-01-31

### Fixed

- Check valid document extension before checking contents when validating documents ([#189](https://github.com/galaxyproject/galaxy-language-server/pull/189)).

## [0.7.0] - 2022-01-29

### Added

- New custom command to discover tests in a single tool file to support the new Testing API in the client ([#183](https://github.com/galaxyproject/galaxy-language-server/pull/183)).

### Changed

- Update `pygls` dependency and fix how custom commands are registered ([#179](https://github.com/galaxyproject/galaxy-language-server/pull/179)).

### Fixed

- An error creating `Code Actions` to extract macros when selecting a text range in some situations ([#178](https://github.com/galaxyproject/galaxy-language-server/pull/178)).

## [0.6.1] - 2021-09-26

### Changed

- Revert `pygls` version to `0.11.1`. This should temporarily fix an issue that prevents using any custom command in the language server ([#172](https://github.com/galaxyproject/galaxy-language-server/pull/172)).

## [0.6.0] - 2021-09-12

### Added

- Code Action language feature to be able to extract macros out of valid blocks of XML ([#165](https://github.com/galaxyproject/galaxy-language-server/pull/165)).

## [0.5.3] - 2021-07-09

### Fixed

- An error when generating tests from inputs that contained boolean values different than `true` or `false` like `True` or `False` ([#156](https://github.com/galaxyproject/galaxy-language-server/pull/156)).

## [0.5.2] - 2021-06-08

### Fixed

- Line offset mismatch between diagnostic line and expanded document ([#150](https://github.com/galaxyproject/galaxy-language-server/pull/150)).

## [0.5.1] - 2021-06-03

### Fixed

- Clear diagnostics when the document is not valid ([#143](https://github.com/galaxyproject/galaxy-language-server/pull/143)).

- Fix empty document validation ([#144](https://github.com/galaxyproject/galaxy-language-server/pull/144)).

## [0.5.0] - 2021-05-13

### Added

- New feature to navigate to (or peek) `macro` and `token` definitions, open referenced macro files directly from the `<import>` tag and preview `token` values on hover ([#127](https://github.com/galaxyproject/galaxy-language-server/pull/127)).

- A custom command to generate the expanded version of a tool document ([#128](https://github.com/galaxyproject/galaxy-language-server/pull/128)).

- Existing macro names are now suggested when manually invoking IntelliSense with `Ctrl+Space` ([#132](https://github.com/galaxyproject/galaxy-language-server/pull/132)).

- Support for dynamic token parameter attributes in `<expand>` elements ([#133](https://github.com/galaxyproject/galaxy-language-server/pull/133)).

### Changed

- Updated main dependencies to latests versions, specially `pygls=0.10.3` which introduced some backward incompatible changes ([#126](https://github.com/galaxyproject/galaxy-language-server/pull/126)).

### Fixed

- When manually invoking IntelliSense with `Ctrl+Space` in the middle of a tag or attribute the auto-completion was suggesting wrong values ([#129](https://github.com/galaxyproject/galaxy-language-server/pull/129)).

- Auto-closing tags when writing `/` or `>` was broken in previous versions ([#137](https://github.com/galaxyproject/galaxy-language-server/pull/137)).

## [0.4.0] - 2021-02-15

### Added

- A custom command for tests discovery that provides information about the test definitions of all the opened tool documents in the virtual workspace ([#110](https://github.com/galaxyproject/galaxy-language-server/pull/110)).

- A custom command to reorder `<param>` attributes according to the IUC Style Guidelines ([#104](https://github.com/galaxyproject/galaxy-language-server/pull/104)).

### Fixed

- Unexpected errors when generating code were failing silently without providing feedback to the user. Now an error notification will be displayed to the user ([#113](https://github.com/galaxyproject/galaxy-language-server/pull/113)).

- Elements inside macros were not correctly associated with their XSD definition ([#111](https://github.com/galaxyproject/galaxy-language-server/pull/111)).

- An bug in the search algorithm when analyzing the tool input trees with nested conditional sharing the same 'when' value. This was causing the code generation commands to fail ([#109](https://github.com/galaxyproject/galaxy-language-server/pull/109)).

## [0.3.2] - 2021-01-24

### Fixed

- The server was ignoring tool wrappers with syntax errors instead of reporting those syntax errors ([#100](https://github.com/galaxyproject/galaxy-language-server/pull/100)).

## [0.3.1] - 2021-01-09

### Fixed

- The autocompletion of tags and attributes was leaking into the `CDATA` sections ([#86](https://github.com/galaxyproject/galaxy-language-server/pull/86)).

- Weird behavior of the autoclosing tag feature ([#86](https://github.com/galaxyproject/galaxy-language-server/pull/86)).

- When using a custom command to auto-generate the `<command>` or the `<tests>` sections (with a tool document containing `macros`), the insert position inside the document for the code snippets was offset ([#83](https://github.com/galaxyproject/galaxy-language-server/pull/83)).

## [0.3.0] - 2021-01-01

### Added

- A custom command to auto-generate the `<command>` section with boilerplate Cheetah template based on the current `inputs` and `outputs` defined in the tool ([#77](https://github.com/galaxyproject/galaxy-language-server/pull/77)).
- A custom command to auto-generate `<test>` cases based on the current `inputs` and `outputs` defined in the tool ([#73](https://github.com/galaxyproject/galaxy-language-server/pull/73)).

### Fixed

- Avoid processing unknown XML documents (aka _not_ tool wrappers) ([#75](https://github.com/galaxyproject/galaxy-language-server/pull/75)).
- Broken XML parsing when more than one comment block was present in the document ([#70](https://github.com/galaxyproject/galaxy-language-server/pull/70)).

## [0.2.1] - 2020-11-22

### Fixed

- The documentation displayed when hovering an element now shows the correct documentation instead of `No documentation available` ([#64](https://github.com/galaxyproject/galaxy-language-server/pull/64)).

## [0.2.0] - 2020-11-13

### Added

- Client settings to control completion features ([#56](https://github.com/galaxyproject/galaxy-language-server/pull/56)).

### Changed

- The XML parser has been replaced with a better implementation ([#55](https://github.com/galaxyproject/galaxy-language-server/pull/55)).

## [0.1.2] - 2020-10-25

### Removed

- Removed unused function `XsdTree.find_node_by_name()`.

## [0.1.1] - 2020-10-24

### Added

- Support autocompletion for `<expand>` element.

### Changed

- Updated dependencies to latest versions.

### Fixed

- Fix error when hovering `<expand>` elements or it's atributes (#41).

## [0.1.0] - 2020-10-14

### Added

- Basic tag and attribute auto-completion.
- Auto-close tags feature.
- XML tool validation when opening and saving file.
- Basic validation of macros.
- Auto-formatting document when saving file.
- Display tag and attribute documentation when hovering.
