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

# Getting Started

## Using the project

If you just want to use the features provided by the Galaxy Language Server, the easiest and recommended option is to **install the VSCode extension** from the [Market](https://marketplace.visualstudio.com/items?itemName=davelopez.galaxy-tools) or, if you prefer, you can use [VSCodium](https://github.com/VSCodium/vscodium) and the [Open VSX registry](https://open-vsx.org/extension/davelopez/galaxy-tools). Additionally, you can download the VSIX package from the [releases](https://github.com/galaxyproject/galaxy-language-server/releases) page and install it manually.

## Contributing

If you are considering contributing, please read the [contribution guide](docs/CONTRIBUTING.md).

To setup your development environment, please check [this guide](docs/CONTRIBUTING.md#getting-started).

# Features

For a complete list of features [check this section](client/README.md#features).

You can also watch a (somewhat old) short video with a tour of some of the features of the Galaxy Tools extension here:

[![Galaxy Tools features video](https://img.youtube.com/vi/MpPrgtNrEcQ/0.jpg)](https://www.youtube.com/watch?v=MpPrgtNrEcQ)
