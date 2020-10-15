"""Galaxy Language Server Setup"""

import os
import pathlib
from setuptools import setup, find_packages


PACKAGE_NAME = "galaxy-language-server"
VERSION = os.environ.get("GALAXYLS_VERSION", "0.0.0")
AUTHOR = "David López"
AUTHOR_EMAIL = "davelopez7391@gmail.com"
DESCRIPTION = "A language server for Galaxy (https://galaxyproject.org) tool wrappers"
KEYWORDS = ["galaxy", "python", "language server"]
LICENSE = "Apache License 2.0"
URL = "https://github.com/davelopez/galaxy-language-server/tree/master/server"

base_directory = pathlib.Path(__file__).parent

long_description = (base_directory / "README.md").read_text(encoding="utf-8")
long_description += (base_directory / "CHANGELOG.md").read_text(encoding="utf-8")

requirements = (base_directory / "requirements.txt").read_text().splitlines()

packages = find_packages(exclude=["*.tests*"])

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=URL,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    keywords=KEYWORDS,
    license=LICENSE,
    packages=packages,
    include_package_data=True,
    install_requires=requirements,
    python_requires="~=3.8",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
    ],
)
