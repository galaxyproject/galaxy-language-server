# Galaxy Tools

### Server
Language server implementation in python to assist in developing [Galaxy](https://galaxyproject.org/) tools.

#### Dependencies
* [pygls](https://github.com/openlawlibrary/pygls) generic implementation of the [Language Server Protocol](https://microsoft.github.io/language-server-protocol/specification) in python
* [lxml](https://lxml.de/index.html) python library for processing xml files


### Client
VS Code Extension with the Language Server client implementation.


## Quick Start
### Install Server Dependencies

1. Create python virtual environment `python -m venv env`
1. Select the `env` virtual environment in VS Code (more information [here](https://code.visualstudio.com/docs/python/environments))
1. Install dependencies `pip install -r requirements.txt`


### Install Client Dependencies

Open terminal and execute `npm install`

### Debug

1. Open this directory in VS Code
1. Open debug view (`ctrl + shift + D`)
1. Select `Server + Client` and press `F5`
