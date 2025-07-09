"""Galaxy Language Server Setup"""

import pathlib

from setuptools import (
    find_packages,
    setup,
)

from galaxyls.version import GLS_VERSION

PACKAGE_NAME = "galaxy-language-server"
VERSION = GLS_VERSION
AUTHOR = "David López"
AUTHOR_EMAIL = "davelopez7391@gmail.com"
DESCRIPTION = "A language server for Galaxy (https://galaxyproject.org) tool wrappers"
KEYWORDS = ["galaxy", "python", "language server"]
LICENSE = "Apache-2.0"
URL = "https://github.com/davelopez/galaxy-language-server/tree/main/server"

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
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
