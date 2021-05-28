# Galaxy Tools (Visual Studio Code Extension)

This extension provides XML validation, tags and attributes completion, help/documentation on hover, and other _smart_ features to assist in **following best practices** recommended by the [Intergalactic Utilities Commission](https://galaxy-iuc-standards.readthedocs.io/en/latest/index.html) during the development process of XML tool wrappers for [Galaxy](https://galaxyproject.org/).

> Please note this is still a work in progress so **bugs and issues are expected**. If you find any, you are welcome to open a new [issue](https://github.com/galaxyproject/galaxy-language-server/issues).

# Requirements

## Requires ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/galaxy-language-server)

To use the [Galaxy Language Server](https://pypi.org/project/galaxy-language-server/) features you need Python 3.8+ installed on your system. See the [Installation](#Installation) section for more details.

## Planemo

Since version `0.4.0` you can use some of the cool features of [planemo](https://github.com/galaxyproject/planemo) directly from the extension. You only need to provide the required path to your planemo installation (see [configuration](#planemo-settings)) and the necessary parameters.

## Test Explorer UI (extension)

To support testing your tools using `planemo test` inside VSCode you need to install the [Test Explorer UI](https://marketplace.visualstudio.com/items?itemName=hbenl.vscode-test-explorer) extension. This is a new requirement since version `0.4.0`.

# Table of Content

- [Installation](#installation)
  - [Troubleshooting](#troubleshooting)
- [Configuration](#configuration)
  - [Completion settings](#completion-settings)
  - [Planemo settings](#planemo-settings)
- [Features](#features)
  - [Tag and attribute auto-completion](#tag-and-attribute-auto-completion)
  - [Documentation on Hover](#documentation-on-hover)
  - [Document validation](#document-validation)
  - [Document auto-formatting](#document-auto-formatting)
  - [Tag auto-closing](#tag-auto-closing)
  - [Snippets](#snippets)
  - [Embedded syntax highlighting](#embedded-syntax-highlighting)
  - [Auto-generate tests](#auto-generate-tests)
  - [Auto-generate command section](#auto-generate-command-section)
  - [Auto-sort param attributes](#auto-sort-param-attributes)
  - [Run planemo tests in the Test Explorer](#run-planemo-tests-in-the-test-explorer)
  - [Improved macros support](#improved-macros-support) _New feature!_ :rocket:

# Installation

When the extension is activated for the first time, a notification will pop up informing that the `Galaxy Language Server` [Python package](https://pypi.org/project/galaxy-language-server/) must be installed.

The installation process will try to use the default Python version in your system. If the version is not compatible, it will ask you to enter the path to a compatible version. Just click `Select` in the notification message and you will be able to type the Python path at the top of the window.

This Python version is used to create a virtual environment in which the language server will be installed. Please note that on Debian/Ubuntu systems, you may need to install the `python3-venv` package to be able to create the virtual environment including `pip`, otherwise the installation may fail. Please see the [Troubleshooting](#troubleshooting) section below for more information.

## Troubleshooting

If you encounter any problem during the language server installation, open the Visual Studio Code `Console log` and then find any error message with the `[gls]` prefix. You can access this log from the menu `Help > Toggle Developer Tools > Console`. Then, search the issues [here](https://github.com/galaxyproject/galaxy-language-server/issues) to check whether the problem already has a solution. If not, please feel free to open a new issue including the error message from the console log.

Some possible errors:

- `The selected file is not a valid Python <version> path!`. This message will appear if you select a Python binary that is not compatible with the required version. You will be given a chance to select the correct version the next time the extension gets activated. You can force it by reloading the extension or restarting VScode.

- `Error installing the Galaxy Language Server: pip module not found`. The extension needs to create a virtual environment to install the `galaxy-language-server` package and its dependencies. To create a proper environment with `pip` included, in some systems you need to install the `python3-venv` package using the following command: `apt install python3-venv` (you may need to use `sudo`). Once you have `python3-venv` installed, you may need to remove the `glsenv` directory inside the extension installation directory and then restart or reload VSCode to recreate the environment.

# Configuration

You can customize some of the features with various settings either placing them in the `.vscode/settings.json` file in your workspace or editing them through the Settings Editor UI.

## Completion settings

| Property                               | Description                                                                                                                                                                                                                                                                                                        |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `galaxyTools.completion.mode`          | This setting controls the auto-completion of tags and attributes. You can choose between three different options: `auto` shows suggestions as you type; `invoke` shows suggestions only when you request them using the key shortcut (`Ctrl + space`); `disabled` completely disables the auto-completion feature. |
| `galaxyTools.completion.autoCloseTags` | This setting controls whether to auto-insert the closing tag after typing `>` or `/`.                                                                                                                                                                                                                              |

## Planemo settings

Planemo integration is currently in **experimental** phase. Please report any problems you may encounter [here](https://github.com/galaxyproject/galaxy-language-server/issues).

| Property                         | Description                                                                                                                                                                                                                                                      |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `galaxyTools.planemo.enabled`    | When enabled, you can use some of the `planemo` features directly from your editor. Please set `#galaxyTools.planemo.envPath#` to be able to use `planemo`.                                                                                                      |
| `galaxyTools.planemo.envPath`    | The full path to the `Python virtual environment` where `planemo` is installed. The path must end with `planemo` and be something like `/<full-path-to-virtual-env>/bin/planemo`. **This is required** to be able to use `planemo` features.                     |
| `galaxyTools.planemo.galaxyRoot` | The full path to the _Galaxy root directory_ that will be used by `planemo`. This value will be passed to `planemo` as the parameter to `--galaxy_root`. **This is required** to be able to use _some_ `planemo` features that need a `running Galaxy instance`. |

## Testing Configuration

### Planemo testing configuration

| Property                                                    | Description                                                                             |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `galaxyTools.planemo.testing.enabled`                       | Whether to discover and run tests using `planemo test` directly from the Test Explorer. |
| `galaxyTools.planemo.testing.autoTestDiscoverOnSaveEnabled` | Whether to try to discover new tests when a Galaxy Tool Wrapper file is saved.          |

### Configuring Test Explorer UI

The following additional configuration properties are provided by [Test Explorer UI](https://marketplace.visualstudio.com/items?itemName=hbenl.vscode-test-explorer):

| Property                              | Description                                                                                                                                                                                                                             |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `testExplorer.onStart`                | Retire or reset all test states whenever a test run is started                                                                                                                                                                          |
| `testExplorer.onReload`               | Retire or reset all test states whenever the test tree is reloaded                                                                                                                                                                      |
| `testExplorer.codeLens`               | Show a CodeLens above each test or suite for running or debugging the tests                                                                                                                                                             |
| `testExplorer.gutterDecoration`       | Show the state of each test in the editor using Gutter Decorations                                                                                                                                                                      |
| `testExplorer.errorDecoration`        | Show error messages from test failures as decorations in the editor                                                                                                                                                                     |
| `testExplorer.errorDecorationHover`   | Provide hover messages for the error decorations in the editor                                                                                                                                                                          |
| `testExplorer.sort`                   | Sort the tests and suites by label or location. If this is not set (or set to null), they will be shown in the order that they were received from the adapter                                                                           |
| `testExplorer.showCollapseButton`     | Show a button for collapsing the nodes of the test tree                                                                                                                                                                                 |
| `testExplorer.showExpandButton`       | Show a button for expanding the top nodes of the test tree, recursively for the given number of levels                                                                                                                                  |
| `testExplorer.showOnRun`              | Switch to the Test Explorer view whenever a test run is started                                                                                                                                                                         |
| `testExplorer.addToEditorContextMenu` | Add menu items for running and debugging the tests in the current file to the editor context menu                                                                                                                                       |
| `testExplorer.mergeSuites`            | Merge suites with the same label and parent                                                                                                                                                                                             |
| `testExplorer.hideEmptyLog`           | Hide the output channel used to show a test's log when the user clicks on a test whose log is empty                                                                                                                                     |
| `testExplorer.hideWhen`               | Hide the Test Explorer when no test adapters have been registered or when no tests have been found by the registered adapters. The default is to never hide the Test Explorer (some test adapters only work with this default setting). |

See [Test Explorer UI](https://marketplace.visualstudio.com/items?itemName=hbenl.vscode-test-explorer) documentation for the latest configuration changes.

# Features

## Tag and attribute auto-completion

![Demo feature auto-completion](../assets/feature.autocompletion.gif)

The tags and attributes are suggested based on the [Galaxy.xsd](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/tool_util/xsd/galaxy.xsd) schema. They will appear in the same order that they are declared in the schema, so they can comply with the best practices recommendations defined in the [Galaxy IUC Standards Style Guide](https://galaxy-iuc-standards.readthedocs.io/en/latest/best_practices/tool_xml.html?#coding-style).

## Documentation on Hover

![Demo feature hover documentation](../assets/feature.hover.documentation.gif)

The documentation of tags and attributes is retrieved from the [Galaxy.xsd](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/tool_util/xsd/galaxy.xsd) schema.

> Please note that some elements in the schema are still missing documentation. This will probably be improved over time.

## Document validation

![Demo feature validation](../assets/feature.validation.png)

The tools are also validated against the [Galaxy.xsd](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/tool_util/xsd/galaxy.xsd) schema.

## Document auto-formatting

![Demo feature auto-formatting](../assets/feature.autoformat.gif)

When the tool file is saved it gets auto-formatted to comply with the [Galaxy IUC Standards Style Guide](https://galaxy-iuc-standards.readthedocs.io/en/latest/best_practices/tool_xml.html?#coding-style).

## Tag auto-closing

![Demo feature auto-close tags](../assets/autoCloseTag.gif)

Whenever you write a closing (`>`), the corresponding closing tag will be inserted. You can also type `/` in an open tag to close it.

## Snippets

![Demo snippets](../assets/snippets.gif)

Snippets can be really helpful to speed up your tool wrapper development. They allow you to quickly create common blocks and let you enter just the important information by pressing `tab` and navigating to the next available value.

> If you want to add more snippets check the [guide](./docs/CONTRIBUTING.md#adding-snippets) in the contribution guidelines.

## Embedded syntax highlighting

![Demo feature embedded syntax highlighting](../assets/feature.embedded.syntax.png)

Basic support for `Cheetah` and `reStructuredText` syntax highlighting inside the `<command>`, `<configfile>` and `<help>` tags. The embedded code should be inside a `CDATA` block.

## Auto-generate tests

![Demo feature auto-generate tests](../assets/feature.generate.tests.gif)

After you define the `<inputs>` and `<outputs>` of the tool, you can press `Ctrl+Alt+t` (or `Cmd+Alt+t` in Mac) to create a `<tests>` section with a basic structure and some test cases. This is especially useful when using conditionals and other nested parameters since you can get right away most of the boilerplate XML.

## Auto-generate command section

![Demo feature auto-generate command section](../assets/feature.generate.command.gif)

Similar to the [auto-generate tests](#Auto-generate-tests) command, but this time it will generate boilerplate `Cheetah` code for the `<command>` section.

## Auto-sort param attributes

![Demo feature auto-sort param attributes](../assets/feature.sort.param.attributes.gif)

Now you can automatically sort the attributes of param elements according to the [IUC Coding Style guidelines](https://galaxy-iuc-standards.readthedocs.io/en/latest/best_practices/tool_xml.html#coding-style) using a key-shortcut or the command palette. This can be done for each `<param>` element individually or for the full document.

## Run planemo tests in the Test Explorer

![Demo feature planemo tests explorer](../assets/feature.planemo.testing.png)

You can now run `planemo test` for the currently opened tool directly from the `Test Explorer`.

- The tests are automatically discovered by the `galaxy-language-server` when you open a tool or save the document (this can be controlled by the settings).
- You can then run all the tests from the `Test Explorer` by using `planemo test` in the background. Currently running individual tests is not supported as AFAIK `planemo` does not have an option to do so at the moment.
- After successfully running the tests, the results will be displayed in a convenient way directly on your source XML.

The failing tests will be marked in red and the reason for failure can be seen directly beside the test definition in the same line or more detailed in the `Output`. You can also directly navigate to each of the tests XML source from the `Test Explorer`.
This can be very convenient especially when having a large number of tests in your tool.

## Improved macros support

Since version `0.5.0` we added some interesting features around the use of macros. For example, you can now better troubleshoot validation errors caused by some included macro. The error messages will be more detailed and you can even navigate to a `expanded` version of the tool to see what the real tool document look like and what was causing the error.

![Demo feature expanded macros](../assets/feature.expanded.macros.gif)

There are also a lot of features around macros auto-completion. You can now navigate to `macro` and `token` definitions with `F12` or get dynamic attribute auto-completion with parametrized macros and more.

![Demo feature macros support](../assets/feature.macros.support.gif)
