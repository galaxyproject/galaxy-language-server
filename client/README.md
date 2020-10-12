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
