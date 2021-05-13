# Galaxy Tools Extension and Galaxy Language Server

[![Actions Status](https://github.com/davelopez/galaxy-language-server/workflows/Language%20Server%20CI/badge.svg)](https://github.com/davelopez/galaxy-language-server/actions)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/galaxy-language-server)
[![PyPI](https://img.shields.io/pypi/v/galaxy-language-server?color=green)](https://pypi.org/project/galaxy-language-server/)

This repository contains two projects:

- [**Galaxy Language Server**](https://github.com/davelopez/galaxy-language-server/tree/master/server): [Python](https://www.python.org/) implementation of the [Language Server Protocol](https://microsoft.github.io/language-server-protocol/).
- [**Galaxy Tools extension**](https://github.com/davelopez/galaxy-language-server/tree/master/client): [Visual Studio Code](https://code.visualstudio.com/) [extension](https://marketplace.visualstudio.com/VSCode) in [Node.js](https://nodejs.org/en/).

This project has the following main goals:

- **Encourage best practices**: one of the **most important goals** of this project is to assist the developer in writing tools that follow the [best practices established by the Intergalactic Utilities Commission](https://galaxy-iuc-standards.readthedocs.io/en/latest/index.html) by providing features like [attribute sorting](#auto-sort-param-attributes) or [auto-formatting](#document-auto-formatting) and many more to come!
- **Easy onboarding of new Galaxy tool developers**: with the [intelligent code completion](#tag-and-attribute-auto-completion) and the [documentation tooltips](#documentation-on-hover), new developers can reduce the need for memorizing tags and attributes as well as easily discover what they need as they write avoiding syntax and structural errors on the way.
- **Development speed**: more experienced developers can greatly boost their speed writing tools for Galaxy by using the [code snippets](#snippets) to quickly write code for commonly used tag or even [generating scaffolding code for the tests](#auto-generate-tests) covering most of the _conditional paths_ of their tool.

> Please note this is still a work in progress so **bugs and issues are expected**. If you find any, you are welcome to open a new [issue](https://github.com/galaxyproject/galaxy-language-server/issues).

# Table of Contents

- [Getting Started](#getting-started)
  - [Using the project](#using-the-project)
  - [Contributing](#contributing)
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

# Getting Started

## Using the project

If you just want to use the features provided by the Galaxy Language Server, the easiest and recommended option is to **install the VSCode extension** from the [Market](https://marketplace.visualstudio.com/items?itemName=davelopez.galaxy-tools) or, if you prefer, you can use [VSCodium](https://github.com/VSCodium/vscodium) and the [Open VSX registry](https://open-vsx.org/extension/davelopez/galaxy-tools). Additionally, you can download the VSIX package from the [releases](https://github.com/galaxyproject/galaxy-language-server/releases) page and install it manually.

## Contributing

If you are considering contributing, please read the [contribution guide](docs/CONTRIBUTING.md).

To setup your development environment, please check [this guide](docs/CONTRIBUTING.md#getting-started).

# Features

You can watch a short video with a tour of some of the features of the Galaxy Tools extension here:

[![Galaxy Tools features video](https://img.youtube.com/vi/MpPrgtNrEcQ/0.jpg)](https://www.youtube.com/watch?v=MpPrgtNrEcQ)

## Tag and attribute auto-completion

![Demo feature auto-completion](../assets/feature.autocompletion.gif)

The tags and attributes are suggested based on the [Galaxy.xsd](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/tool_util/xsd/galaxy.xsd) schema. They will appear in the same order as they are declared in the schema to comply with the best practices recommendations defined in the [Galaxy IUC Standards Style Guide](https://galaxy-iuc-standards.readthedocs.io/en/latest/best_practices/tool_xml.html?#coding-style).

## Documentation on Hover

![Demo feature hover documentation](../assets/feature.hover.documentation.gif)

The documentation of tags and attributes is retrieved from the [Galaxy.xsd](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/tool_util/xsd/galaxy.xsd) schema.

> Please note that some elements in the schema are still missing documentation. This will probably be improved over time.

## Document validation

![Demo feature validation](../assets/feature.validation.png)

The tools are also validated against the [Galaxy.xsd](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/tool_util/xsd/galaxy.xsd) schema.

## Document auto-formatting

![Demo feature auto-formatting](../assets/feature.autoformat.gif)

When the tool file is saved it gets auto-formatted to maintain a consistent format with the [Galaxy IUC Standards Style Guide](https://galaxy-iuc-standards.readthedocs.io/en/latest/best_practices/tool_xml.html?#coding-style).

## Tag auto-closing

![Demo feature auto-close tags](../assets/autoCloseTag.gif)

Whenever you write a closing (`>`), the corresponding closing tag will be inserted. You can also type `/` in an open tag to close it.

## Snippets

![Demo snippets](../assets/snippets.gif)

Snippets can be really helpful to speed up your tool wrapper development. They allow to quickly create common blocks and let you enter just the important information by pressing `tab` and navigating to the next available value.

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
