# Galaxy Language Server
[![Actions Status](https://github.com/davelopez/galaxy-language-server/workflows/Language%20Server%20CI/badge.svg)](https://github.com/davelopez/galaxy-language-server/actions)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/galaxy-language-server)
[![PyPI version](https://badge.fury.io/py/galaxy-language-server.svg)](https://badge.fury.io/py/galaxy-language-server)

[Language Server](https://microsoft.github.io/language-server-protocol/) implementation written in Python ([pygls](https://github.com/openlawlibrary/pygls)) to assist in the development of [Galaxy tool wrappers](https://docs.galaxyproject.org/en/latest/dev/schema.html).

#### Dependencies
* [pygls](https://github.com/openlawlibrary/pygls): generic implementation of the [Language Server Protocol](https://microsoft.github.io/language-server-protocol/specification) in Python.
* [lxml](https://lxml.de/index.html): Python library for processing XML files.
* [anytree](https://github.com/c0fec0de/anytree): Python library with an easy to use tree structure.
* [galaxy-tool-util](https://pypi.org/project/galaxy-tool-util/): the [Galaxy](https://galaxyproject.org/) tool utilities for Python.


# Getting Started
Check the [Getting Started](https://github.com/galaxyproject/galaxy-language-server/blob/master/docs/CONTRIBUTING.md#getting-started) section in the [contributing](https://github.com/galaxyproject/galaxy-language-server/blob/master/docs/CONTRIBUTING.md) docs.

# How to manually run the server
Usually, the [client](https://github.com/galaxyproject/galaxy-language-server/tree/master/client) will be in charge of running the server when it is needed, but, in case you want to run it manually for some reason, you can use the following commands:

In any case, it is recommended to create a Python virtual environment first (assuming you are using `Python3.8+`):
````sh
# Create a virtual environment and activate it
python -m venv myenv
source ./myenv/bin/activate
````

## Option 1: Installing from PyPi
````sh
# Install the language server and its dependencies
pip install galaxy-language-server
````

## Option 2: Building from source
````sh
# Clone the repo
git clone https://github.com/galaxyproject/galaxy-language-server.git

# Go to the server directory
cd galaxy-language-server/server

# Install the dependencies
python -m pip install -r ./requirements.txt
````

## Run the server
````sh
# Run the server with the default parameters
python -m galaxyls
````

By default, the server uses IO pipes to communicate with the client. If you want to use TCP, you can pass additional parameters, for example:

````sh
python -m galaxyls --tcp --host=127.0.0.1 --port=2087
````

To check if everything went ok, you can look at the content of the server log file (``galaxy-language-server.log``) that should contain the following lines:
````
INFO:pygls.server:Starting server on 127.0.0.1:2087
INFO:pygls.server:Shutting down the server
INFO:pygls.server:Closing the event loop.
````
