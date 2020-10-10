# Contributing Guide

First off, **thank you** for considering contributing to this project! We really appreciate it as we can learn from each other and achieve better things together! :rocket:

Following these guidelines indicates that you respect the time of the maintainers of this open-source project. In return, they will be happy to help you address your issues and pull requests.

## Code of Conduct
This project, and everyone participating in it, are governed by the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behaviour to [beatrizserrano.galaxy@gmail.com](mailto:beatrizserrano.galaxy@gmail.com).

## How can I contribute?
Here are some ideas of how to contribute to this project:

### Reporting Bugs
You can report bugs by creating a new [issue](https://github.com/davelopez/galaxy-language-server/issues). Please, before opening a new issue, make sure there is no duplicate by looking for the [bug](https://github.com/davelopez/galaxy-language-server/issues?q=is%3Aissue+is%3Aopen+label%3Abug) tag first.

When creating the issue, explain the problem and include additional details to help maintainers reproduce the problem:

* **Use a clear and descriptive title** for the issue to identify the problem.
* **Describe the exact steps that reproduce the problem** in as many details as possible. When listing steps, **don't just say what you have done but explain how you did it**.
* **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
* **Explain which behavior you expected to see instead and why.**
* **Include screenshots and animated GIFs** which show you following the described steps and clearly demonstrate the problem. You can use, for example, [this tool](https://www.cockos.com/licecap/) to record GIFs on macOS and Windows.
* **Include details about your environment**, the version of the extension, your Operating System, configuration files, and all the relevant information that you can provide.

In general, when filing an issue, make sure to answer these five questions:

1. What version of the extension are you using?
2. What version of Visual Studio Code are you using?
3. What OS and processor architecture are you using?
4. What did you do?
5. What did you expect to see?
6. What did you see instead?

### Suggesting Features or Enhancements
If you have an idea to add new features that can improve the utility and provide better experiences for the Galaxy tool development process, we are happy to hear it!

Just create a new [issue](https://github.com/davelopez/galaxy-language-server/issues), but always making sure there is no duplicate by looking for the [enhancement](https://github.com/davelopez/galaxy-language-server/issues?q=label%3Aenhancement+) tag first. Then, provide the following information:
* **Use a clear and descriptive title** for the issue to identify the suggestion.
* **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
* **Describe the current behavior** and **explain which behavior you expected to see instead** and why.
* **Explain why this enhancement would be useful** to most Galaxy tool developers.
* **List some other entensions or Language Servers where this enhancement exists.**

### Fixing Bugs
If you want to help improving the quality of the [extension](../client) or the [Language Server](../server), look for the [bug](https://github.com/davelopez/galaxy-language-server/issues?q=is%3Aissue+is%3Aopen+label%3Abug) tag in the project's issues and pick one to fix :)

Just make sure you create a **new failing test case that your patch solves** and include it in your pull request.

See the [Getting started](#getting-started) section for a detailed guide on how to create a pull request.

### Implementing features
Implementing new features can be challenging but also really fun! Usually, we try to focus first on fixing any open bugs before trying to implement new things, but if you want to help with a new feature, make sure to have a look at the projects panel and the milestones to have an idea on which feature better fits the project roadmap.

When issuing a pull request with a new feature make sure you:

1. Provide **enough tests to cover the common and edge cases** that the new feature may create.
2. Provide **good quality code documentation** for methods and classes.
3. Follow the [Style Guide](#style-guide).

See the [Getting started](#getting-started) section for a detailed guide on how to create a pull request.

### Adding or improving documentation
We try to keep good quality and up to date documentation to help everyone understand what is the intention of a particular method or class, or how a particular feature works, but this is not always easy, so, any help with it is much appreciated!

Even spelling/grammar, typo corrections, are much appreciated!

### Adding Snippets
If you want to contribute new snippets to accelerate your tool development or quickly write repetitive and common blocks, this is the place!

Adding a new snippet is really easy, you just need to edit the [snippets.json](../client/src/snippets.json) file and write a ``new entry with the name of your snippet`` and the following data:
- ``prefix``: defines one or more trigger words that display the snippet in IntelliSense. To differentiate Galaxy tool snippets, they should start with ``gx-`` and then some word that identifies your snippet.
- ``body``: here you define a list with the lines composing your snippet. These lines can use special constructs to control cursors and the text being inserted. See this [guide](https://code.visualstudio.com/docs/editor/userdefinedsnippets#_snippet-syntax) for more information.
- ``description``: here you can write a description for you snippet that will be shown in IntelliSense.

After testing your snippet in your local environment, just make a pull request and share it!

# Your First Contribution
If this is your first time... congratulations! :tada: You will learn lots of things! For example, you can find a great number of resources [here](https://github.com/freeCodeCamp/how-to-contribute-to-open-source).

After you have some basic knowledge about how to contribute to open source projects we recommend to search for issues with the [good first issue](https://github.com/davelopez/galaxy-language-server/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22) tag, if there is none, maybe you can come up with some small improvement idea by examining the source code.

At this point, you're ready to make your changes! Feel free to ask for help; everyone is a beginner at first :smile_cat:


# Getting started
Finally some action!

We recommend to use VSCode or the open source alternative [VSCodium](https://vscodium.com/) for local development.

To install the dependencies we also recommend using [miniconda](https://docs.conda.io/en/latest/miniconda.html) with ``Python 3.8``.

If you are using `Windows` we recommend installing and using [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10#install-your-linux-distribution-of-choice) for a better Linux-like shell command experience.

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
    Now you can make your changes locally.
    
    Remember to check the [Style Guide](#style-guide) to maintain an uniform code style.

6. When you're done making changes, check that your changes pass ``style linter`` and the ``tests``.
    ```sh
    flake8
    pytest
    ```

7. Commit your changes and push your branch to GitHub:
    ```sh
    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature
    ```

8. Submit a pull request through the GitHub website.

### Setup Visual Studio Code for debugging
If you want to debug the [extension](../client) and the [Language Server](../server) at the same time, follow these steps:
1. Open the `galaxy-tool-extension` directory in Visual Studio Code
2. Open debug view (`ctrl + shift + D`)
3. Select `Server + Client` and press `F5`

## Pull Request Guidelines

Before you submit a pull request, check that it meets the following guidelines:

1. Provide a **detailed description** about the context or motivation of the pull request.
2. If the pull request adds functionality, please remember to **add or update the documentation**.
3. Check **all the tests are passing**.
4. The [Style Guide](#style-guide) is respected.


# Code review process
The maintainers will check regularly if there are any open pull requests and review them, but remember this is an open-source project and they do it on their spare time for fun.

Just have a little patience, if everything is in order your pull request will be merged or you will get some feedback! :smile_cat:


# Style Guide
Currently the style guide is only defined for the [Language Server](../server) which is writen in ``Python``.

Basically you can rely on [flake8](https://pypi.org/project/flake8/) and [black](https://github.com/psf/black) (along with the configuration files provided in the project directory) to manage all the styling for you. If you installed the [development requirements](../requirements-dev.txt) you already have them installed :)
