# Galaxy Language Server Changelog

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
