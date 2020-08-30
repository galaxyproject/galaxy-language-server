# Galaxy Tools (Extension)

> The idea is to provide realtime XML validation, code completion, help/documentation and other features to help in following best practices during the development process of XML tool wrappers for Galaxy.

[![Actions Status](https://github.com/davelopez/galaxy-tools-extension/workflows/CI/badge.svg)](https://github.com/davelopez/galaxy-tools-extension/actions)

The aim of this project is to implement the [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) to assist in the development of [Galaxy tool wrappers](https://docs.galaxyproject.org/en/latest/dev/schema.html) inside modern code editors.

This repository contains both, the [server](https://github.com/davelopez/galaxy-tools-extension/tree/master/server) implementation in [Python](https://www.python.org/) and the [client](https://github.com/davelopez/galaxy-tools-extension/tree/master/client) implementation of a [Visual Studio Code](https://code.visualstudio.com/) [extension](https://marketplace.visualstudio.com/VSCode) in [Node.js](https://nodejs.org/en/).

## Release History
* 0.0.1
    * Work in progress


## Development setup
Clone this repo
```sh
git clone https://github.com/davelopez/galaxy-tools-extension.git
cd galaxy-tools-extension
```
### Install Dependencies

**On Linux & OSX using Conda**
```sh
# create the virtual environment for Python 3.8
conda create -n <environment-name> python=3.8
conda activate <environment-name>

# for the server:
pip install -r requirements-dev.txt

# for the client:
conda install nodejs typescript
npm install
```

**On Windows**

For the server:

Install [Python 3.8](https://docs.python.org/3/using/windows.html#windows-full)
```sh
# create the virtual environment
python -m venv env

# activate the virtual environment
.\env\Scripts\activate
```
Or select the `venv` virtual environment in Visual Studio Code (more information [here](https://code.visualstudio.com/docs/python/environments))
```sh
# Install dependencies
pip install -r requirements-dev.txt
```

For the client:

Install [Node.js](https://nodejs.org/en/download/)

Open terminal in the `galaxy-tools-extension` directory where the `package.json` file is in
```sh
npm install
```


### Debug Server + Client in Visual Studio Code

1. Open the `galaxy-tool-extension` directory in Visual Studio Code
1. Open debug view (`ctrl + shift + D`)
1. Select `Server + Client` and press `F5`
