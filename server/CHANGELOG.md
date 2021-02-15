# Galaxy Language Server Changelog

## [0.4.0] - 2021-02-15

### Added

- A custom command for tests discovery that provides information about the test definitions of all the opened tool documents in the virtual workspace. ([#110](https://github.com/galaxyproject/galaxy-language-server/pull/110))

- A custom command to reorder `<param>` attributes according to the IUC Style Guidelines. ([#104](https://github.com/galaxyproject/galaxy-language-server/pull/104))

### Fixed

- Unexpected errors when generating code were failing silently without providing feedback to the user. Now an error notification will be displayed to the user. ([#113](https://github.com/galaxyproject/galaxy-language-server/pull/113))

- Elements inside macros were not correctly associated with their XSD definition. ([#111](https://github.com/galaxyproject/galaxy-language-server/pull/111))

- An bug in the search algorithm when analyzing the tool input trees with nested conditional sharing the same 'when' value. This was causing the code generation commands to fail. ([#109](https://github.com/galaxyproject/galaxy-language-server/pull/109))

## [0.3.2] - 2021-01-24

### Fixed

- The server was ignoring tool wrappers with syntax errors instead of reporting those syntax errors ([#100](https://github.com/galaxyproject/galaxy-language-server/pull/100))

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

- Avoid processing unknown XML documents (aka *not* tool wrappers) ([#75](https://github.com/galaxyproject/galaxy-language-server/pull/75)).
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

- Removed unused function ``XsdTree.find_node_by_name()``.

## [0.1.1] - 2020-10-24

### Added

- Support autocompletion for ``<expand>`` element.

### Changed

- Updated dependencies to latest versions.

### Fixed

- Fix error when hovering ``<expand>`` elements or it's atributes (#41).


## [0.1.0] - 2020-10-14

### Added

- Basic tag and attribute auto-completion.
- Auto-close tags feature.
- XML tool validation when opening and saving file.
- Basic validation of macros.
- Auto-formatting document when saving file.
- Display tag and attribute documentation when hovering.
