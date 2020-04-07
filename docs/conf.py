"""Sphinx configuration."""
from datetime import datetime


project = "Poetry Up"
author = "Claudio Jolowicz"
copyright = f"{datetime.now().year}, {author}"
extensions = [
    "recommonmark",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]
