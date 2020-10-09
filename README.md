# Galaxy Language Server

[![Actions Status](https://github.com/davelopez/galaxy-tools-extension/workflows/CI/badge.svg)](https://github.com/davelopez/galaxy-tools-extension/actions)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

The aim of this project is to implement the [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) to assist in the development of [Galaxy tool wrappers](https://docs.galaxyproject.org/en/latest/dev/schema.html) inside modern code editors.

> The idea is to provide realtime XML validation, code completion, help/documentation and other *smart* features to help in following best practices during the development process of XML tool wrappers for Galaxy.

This repository contains both the [server](https://github.com/davelopez/galaxy-tools-extension/tree/master/server) implementation in [Python](https://www.python.org/) and the [client](https://github.com/davelopez/galaxy-tools-extension/tree/master/client) implementation of a [Visual Studio Code](https://code.visualstudio.com/) [extension](https://marketplace.visualstudio.com/VSCode) in [Node.js](https://nodejs.org/en/).

> Please note this is still an early work in progress and **bugs and issues are expected**.

## Features
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

---

## Release History

Current version: **``Unreleased``**

See the [change log](docs/CHANGELOG.md) for details.

---

# Getting Started
If you are considering contributing, please read the [contribution guide](docs/CONTRIBUTING.md).

## Setup for local development

1. Fork this repo on Github
2. Clone your fork locally:
    ````sh
    git clone https://github.com/<your_github_name>/galaxy-tools-extension.git
    ````
3. Create a virtual environment using conda and install the dependencies:

    ```sh
    conda create -n <environment-name> python=3.8
    conda activate <environment-name>

    # For the language server:
    pip install -r requirements-dev.txt

    # For the client extension:
    conda install nodejs typescript
    npm install
    ```
4. Run the tests locally
    ```sh
    # For the language server:
    pytest
    # Additionally you can check the coverage:
    pytest --cov=server
    ```

5. Create a branch for local development:

    ```sh
    git checkout -b name-of-your-bugfix-or-feature
    ```
    >Now you can make your changes locally.
    >
    >Remember to check the [Style Guide](#style-guide) to maintain an uniform code style.

6. When you're done making changes, check that your changes pass ``style linter`` and the ``tests``.
    ```sh
    flake8
    pytest
    ```

7. Commit your changes and push your branch to GitHub::
    ```sh
    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature
    ```

8. Submit a pull request through the GitHub website.


### Setup Visual Studio Code for debugging
If you want to debug the [extension](../client) and the [Language Server](../server) at the same time follow these steps:
1. Open the `galaxy-tool-extension` directory in Visual Studio Code
2. Open debug view (`ctrl + shift + D`)
3. Select `Server + Client` and press `F5`
