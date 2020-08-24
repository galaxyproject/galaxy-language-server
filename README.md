# Galaxy Tools

[![Build Status](https://travis-ci.com/davelopez/galaxy-tools-extension.svg?branch=master)](https://travis-ci.com/davelopez/galaxy-tools-extension)

The aim of this project is to implement the [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) to assist in the development of [Galaxy tool wrappers](https://docs.galaxyproject.org/en/latest/dev/schema.html) inside modern code editors. The idea is to provide realtime XML validation, code completion, help/documentation and best practices suggestions to assist in the development process of XML tool wrappers for Galaxy.

This repository contains both, the [server](https://github.com/davelopez/galaxy-tools-extension/tree/master/server) implementation in [Python](https://www.python.org/) and the [client](https://github.com/davelopez/galaxy-tools-extension/tree/master/client) implementation of a [Visual Studio Code](https://code.visualstudio.com/) [extension](https://marketplace.visualstudio.com/VSCode) in [Node.js](https://nodejs.org/en/).

## Quick Start
### Install Dependencies

#### On Unix/OSX using Conda
```sh
conda create -n <environment-name> python=3.8
conda activate <environment-name>
pip install -r requirements.txt
conda install nodejs
npm install
```

#### On Windows

For the server:
1. Install [Python 3.8](https://docs.python.org/3/using/windows.html#windows-full)
1. Create python virtual environment `python -m venv <environment-name>`
1. Select the `<environment-name>` virtual environment in Visual Studio Code (more information [here](https://code.visualstudio.com/docs/python/environments))
1. Install dependencies `pip install -r requirements.txt`

For the client:
1. Install [Node.js](https://nodejs.org/en/download/)
1. Open terminal in the `galaxy-tools-extension` directory where the `package.json` file is in
1. Run `npm install` command


### Debug Server + Client in Visual Studio Code

1. Open the `galaxy-tool-extension` directory in Visual Studio Code
1. Open debug view (`ctrl + shift + D`)
1. Select `Server + Client` and press `F5`
