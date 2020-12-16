# Test Files
This directory contains XML files of tool wrappers that can be used for testing some of the features of the language server.

## Using the files
There are a couple of utility functions to [read the contents](https://github.com/galaxyproject/galaxy-language-server/pull/73/commits/0b60bd290ed66a9082729192667c1abeac418bb1) of these files or to use them as [Document](https://github.com/galaxyproject/galaxy-language-server/pull/73/commits/b4b3d89228ac3b1646ca45fe33a137c588e5c8df) objects.

For example, to get a `Document` object from one of the files, you can use the following:

````Python
from pygls.workspace import Document
from .utils import TestUtils

document: Document = TestUtils.get_test_document_from_file("simple_conditional_01.xml")
````
> Note that you only have to specify the file name.

## How to add more tests

### The [Test Case Generator Command](https://github.com/galaxyproject/galaxy-language-server/pull/73/commits/094dd0abff29eeb6185e5cf10ec6791501b5abcf)

This server's custom command automatically generates multiple test cases from the inputs and outputs of a tool wrapper. The resulting tests are returned as a [code snippet](https://code.visualstudio.com/docs/editor/userdefinedsnippets) that can be inserted in the ``<tests>`` section of a tool document.

To add a new test case with a different set of inputs and outputs and the resulting expected code snippet, we can add two files to this directory using this recommended naming rule:
- Tool file: `<short_description>_<number>.xml` (for example, `simple_conditional_01.xml`)
- Expected generated test snippet: `<short_description>_<number>_test.xml` (for example, `simple_conditional_01_test.xml`)

Once we have our files in this directory, we can add a new test case to check if the generated tests snippet matches the expected. This can be done simply by adding a couple of new parameters with the name of the files to this [parameterized test](https://github.com/galaxyproject/galaxy-language-server/pull/73/commits/5aacebc6904cf83a749b1ba2c9c06b3d64c3b83b#diff-f42181b631232d132f47425e870011e7b9b84afc2d32dec58af467ca0c879b0bR103-R109).