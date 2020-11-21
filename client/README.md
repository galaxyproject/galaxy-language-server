# Galaxy Tools (Visual Studio Code Extension)
This extensions provides XML validation, tag and attribute completion, help/documentation on hover and other *smart* features to assist in following best practices during the development process of XML tool wrappers for [Galaxy](https://galaxyproject.org/).

> Please note this is still an early work in progress so **bugs and issues are expected**.

# Requires ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/galaxy-language-server)
In order to use the [Galaxy Language Server](https://pypi.org/project/galaxy-language-server/) features you need Python 3.8+ installed in your system.

# Features
### Tag and attribute auto-completion 

![Demo feature auto-completion](../assets/feature.autocompletion.gif)

The tags and attributes are suggested based on the [Galaxy.xsd](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/tool_util/xsd/galaxy.xsd) schema. They will appear in the same order that they are declared in the schema, so they can comply with the best practices recommendations defined in the [Galaxy IUC Standards Style Guide](https://galaxy-iuc-standards.readthedocs.io/en/latest/best_practices/tool_xml.html?#coding-style).


### Documentation on Hover

![Demo feature hover documentation](../assets/feature.hover.documentation.gif)

The documentation of tags and attributes is retrieved from the [Galaxy.xsd](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/tool_util/xsd/galaxy.xsd) schema.
>Please note that some elements in the schema are still missing documentation. This will probably be improved over time.


### Document validation

![Demo feature validation](../assets/feature.validation.png)

The tools are also validated against the [Galaxy.xsd](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/tool_util/xsd/galaxy.xsd) schema.


### Document auto-formatting

![Demo feature auto-formatting](../assets/feature.autoformat.gif)

When the tool file is saved it gets auto-formatted to maintain a consistent format with the [Galaxy IUC Standards Style Guide](https://galaxy-iuc-standards.readthedocs.io/en/latest/best_practices/tool_xml.html?#coding-style).

### Tag auto-closing

![Demo feature auto-close tags](../assets/autoCloseTag.gif)

Whenever you write a closing ``>`` the corresponding closing tag will be inserted. You can also type ``/`` in an open tag to close it.


### Snippets

![Demo snippets](../assets/snippets.gif)

Snippets can be really helpful to speed up your tool wrapper development. They allow to quickly create common blocks and let you enter just the important information by pressing ``tab`` and navigating to the next available value.
>If you want to add more snippets check the [guide](./docs/CONTRIBUTING.md#adding-snippets) in the contribution guidelines.

# Installation
When the extension is activated for the first time, a notification will pop up informing that the `Galaxy Language Server` [Python package](https://pypi.org/project/galaxy-language-server/) must be installed.

The installation process will try to use the default Python version in your system. If the version is not compatible, it will ask you to enter the path to a compatible version. Just click `Select` in the notification message and you will be able to type the Python path at the top of the window.

This Python is used to create the virtual environment in which the language server will be installed.

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
This setting ontrols whether to auto-insert the closing tag after typing `>` or `/`.

````json
{
    "galaxyTools.completion.autoCloseTags": false
}
````
