# Galaxy Tools (Extension)

> The idea is to provide realtime XML validation, code completion, help/documentation and other features to help in following best practices during the development process of XML tool wrappers for Galaxy.

[![Actions Status](https://github.com/davelopez/galaxy-tools-extension/workflows/CI/badge.svg)](https://github.com/davelopez/galaxy-tools-extension/actions)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

The aim of this project is to implement the [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) to assist in the development of [Galaxy tool wrappers](https://docs.galaxyproject.org/en/latest/dev/schema.html) inside modern code editors.

This repository contains both the [server](https://github.com/davelopez/galaxy-tools-extension/tree/master/server) implementation in [Python](https://www.python.org/) and the [client](https://github.com/davelopez/galaxy-tools-extension/tree/master/client) implementation of a [Visual Studio Code](https://code.visualstudio.com/) [extension](https://marketplace.visualstudio.com/VSCode) in [Node.js](https://nodejs.org/en/).

## Features
* Basic tag and attribute auto-completion 
* Documentation on Hover
* Document validation based on the [Galaxy.xsd](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/tool_util/xsd/galaxy.xsd)
* Document auto-formatting

    ![Demo Animation](../assets/features.gif)

* Tag auto-closing

    ![Demo Animation](../assets/autoCloseTag.gif)

* Snippets

    ![Demo Animation](../assets/snippets.gif)
    
    >If you want to add more snippets check the [guide](./docs/CONTRIBUTING.md#adding-snippets) in the contribution guidelines.

## Release History

Current version: **``Unreleased``**

See the [change log](docs/CHANGELOG.md) for details.


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
