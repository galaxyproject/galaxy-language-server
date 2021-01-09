# Galaxy Tools (Visual Studio Code Extension)
This extension provides XML validation, tag and attributes completion, help/documentation on hover, and other *smart* features to assist in following best practices during the development process of XML tool wrappers for [Galaxy](https://galaxyproject.org/).

> Please note this is still a work in progress so **bugs and issues are expected**. If you find any, you are welcome to open a new [issue](https://github.com/galaxyproject/galaxy-language-server/issues).

# Requires ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/galaxy-language-server)
In order to use the [Galaxy Language Server](https://pypi.org/project/galaxy-language-server/) features you need Python 3.8+ installed in your system. See the [Installation](#Installation) section for more details.

# Table of Content
- [Installation](#installation)
  - [Troubleshooting](#troubleshooting)
- [Configuration](#configuration)
  - [Completion: mode](#completion-mode)
  - [Completion: auto close tags](#completion-auto-close-tags)
- [Features](#features)
  - [Tag and attribute auto-completion ](#tag-and-attribute-auto-completion-)
  - [Documentation on Hover](#documentation-on-hover)
  - [Document validation](#document-validation)
  - [Document auto-formatting](#document-auto-formatting)
  - [Tag auto-closing](#tag-auto-closing)
  - [Snippets](#snippets)
  - [Embedded syntax highlighting](#embedded-syntax-highlighting)
  - [Auto-generate tests](#auto-generate-tests) *new feature!* :rocket:
  - [Auto-generate command section](#auto-generate-command-section) *new feature!* :rocket:


# Installation
When the extension is activated for the first time, a notification will pop up informing that the `Galaxy Language Server` [Python package](https://pypi.org/project/galaxy-language-server/) must be installed.

The installation process will try to use the default Python version in your system. If the version is not compatible, it will ask you to enter the path to a compatible version. Just click `Select` in the notification message and you will be able to type the Python path at the top of the window.

This Python is used to create a virtual environment in which the language server will be installed.

## Troubleshooting
If you encounter any problem during the language server installation, open the Visual Studio Code `Console log` and then find any error message with the `[gls]` prefix. You can access this log from the menu `Help > Toggle Developer Tools > Console`. Then, search the issues [here](https://github.com/galaxyproject/galaxy-language-server/issues) to check whether the problem already has a solution. If not, please feel free to open a new issue including the error message from the console log.

Some possible errors:
- ``The selected file is not a valid Python <version> path!``. This message will appear if you select a Python binary that is not compatible with the required version. You will be given a chance to select the correct version the next time the extension gets activated. You can force it by reloading the extension or restarting VScode.

# Configuration
You can customize some of the features with various settings either placing them in the settings.json file in your workspace or editing them through the Settings Editor UI.

## Completion: mode
This setting controls the auto-completion of tags and attributes. You can choose between three different options:
- `auto`: shows suggestions as you type. This is the default option.
- `invoke`: shows suggestions only when you request them using the key shortcut (`Ctrl + space`)
- `disabled`: completely disables the auto-completion feature.

````json
{
    "galaxyTools.completion.mode": "invoke",
}
````

## Completion: auto close tags
This setting controls whether to auto-insert the closing tag after typing `>` or `/`.

````json
{
    "galaxyTools.completion.autoCloseTags": false
}
````

# Features
## Tag and attribute auto-completion 

![Demo feature auto-completion](../assets/feature.autocompletion.gif)

The tags and attributes are suggested based on the [Galaxy.xsd](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/tool_util/xsd/galaxy.xsd) schema. They will appear in the same order that they are declared in the schema, so they can comply with the best practices recommendations defined in the [Galaxy IUC Standards Style Guide](https://galaxy-iuc-standards.readthedocs.io/en/latest/best_practices/tool_xml.html?#coding-style).


## Documentation on Hover

![Demo feature hover documentation](../assets/feature.hover.documentation.gif)

The documentation of tags and attributes is retrieved from the [Galaxy.xsd](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/tool_util/xsd/galaxy.xsd) schema.
>Please note that some elements in the schema are still missing documentation. This will probably be improved over time.


## Document validation

![Demo feature validation](../assets/feature.validation.png)

The tools are also validated against the [Galaxy.xsd](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/tool_util/xsd/galaxy.xsd) schema.


## Document auto-formatting

![Demo feature auto-formatting](../assets/feature.autoformat.gif)

When the tool file is saved it gets auto-formatted to maintain a consistent format with the [Galaxy IUC Standards Style Guide](https://galaxy-iuc-standards.readthedocs.io/en/latest/best_practices/tool_xml.html?#coding-style).

## Tag auto-closing

![Demo feature auto-close tags](../assets/autoCloseTag.gif)

Whenever you write a closing ``>`` the corresponding closing tag will be inserted. You can also type ``/`` in an open tag to close it.


## Snippets

![Demo snippets](../assets/snippets.gif)

Snippets can be really helpful to speed up your tool wrapper development. They allow you to quickly create common blocks and let you enter just the important information by pressing ``tab`` and navigating to the next available value.
>If you want to add more snippets check the [guide](./docs/CONTRIBUTING.md#adding-snippets) in the contribution guidelines.

## Embedded syntax highlighting

![Demo feature embedded syntax highlighting](../assets/feature.embedded.syntax.png)

Basic support for `Cheetah` and `reStructuredText` syntax highlighting inside the `<command>`, `<configfile>` and `<help>` tags. The embedded code should be inside a `CDATA` block.

## Auto-generate tests

![Demo feature auto-generate tests](../assets/feature.generate.tests.gif)

After you define the `<inputs>` and `<outputs>` of the tool, you can press `Ctrl+Alt+t` (or `Cmd+Alt+t` in Mac) to create a `<tests>` section with a basic structure and some test cases. This is especially useful when using conditionals and other nested parameters since you can get right away most of the boilerplate XML.

## Auto-generate command section

![Demo feature auto-generate command section](../assets/feature.generate.command.gif)

Similar to the [auto-generate tests](#Auto-generate-tests) command, but this time it will generate boilerplate `Cheetah` code for the `<command>` section.