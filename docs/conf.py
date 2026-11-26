"""Sphinx configuration for the QumPy documentation.

Build locally:   sphinx-build -b html docs docs/_build/html
Then open docs/_build/html/index.html in a browser.
"""

import shutil
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent
ROOT = DOCS.parent
sys.path.insert(0, str(ROOT))          # import qumpy from the repository itself

import qumpy  # noqa: E402

# -- Project ----------------------------------------------------------------
project = "QumPy"
author = "QumPy contributors"
copyright = "2026, QumPy contributors"
release = qumpy.__version__
version = release

# -- Extensions -------------------------------------------------------------
extensions = [
    "myst_nb",                      # Markdown pages + Jupyter notebooks
    "sphinx.ext.autodoc",           # API pages from docstrings
    "sphinx.ext.napoleon",          # NumPy-style "Parameters" sections
    "sphinx.ext.viewcode",          # [source] links
    "sphinx.ext.intersphinx",       # links to Python / NumPy / Qiskit docs
    "sphinx_copybutton",            # copy button on code blocks
]

source_suffix = {".rst": "restructuredtext", ".md": "myst-nb", ".ipynb": "myst-nb"}
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

myst_enable_extensions = ["colon_fence", "deflist", "dollarmath"]
myst_heading_anchors = 3            # so links like installation.md#common-errors work

nb_execution_mode = "off"           # show the notebooks with their saved outputs

autodoc_member_order = "bysource"
autodoc_default_options = {"members": True, "undoc-members": False, "show-inheritance": False}
autodoc_typehints = "description"
napoleon_numpy_docstring = True
napoleon_google_docstring = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "qiskit": ("https://quantum.cloud.ibm.com/docs/api/qiskit", None),
}
intersphinx_timeout = 10

# -- HTML -------------------------------------------------------------------
html_theme = "furo"
html_title = f"QumPy {release}"
html_static_path = []
html_theme_options = {
    "source_repository": "https://github.com/yigitcaneym/QumPy",
    "source_branch": "main",
    "source_directory": "docs/",
}

# The example notebooks live in ../examples; copy them next to the docs so
# Sphinx can render them (the copies are ignored by git).
_EXAMPLES_SRC = ROOT / "examples"
_EXAMPLES_DST = DOCS / "examples"
_EXAMPLES_DST.mkdir(exist_ok=True)
for nb in _EXAMPLES_SRC.glob("*.ipynb"):
    shutil.copy2(nb, _EXAMPLES_DST / nb.name)


# -- Docstring clean-up for the website ---------------------------------------
# QumPy's docstrings are written to read well in help(): they contain kets
# such as |0> and |psi><psi|, and module docstrings start with indented
# example blocks. In reStructuredText "|...|" means a substitution and an
# indented block after a paragraph is a quote (its line breaks are lost).
# This hook fixes both for the website only; help() output is unchanged.
import re  # noqa: E402

_INLINE_LITERAL = re.compile(r"(``.+?``)")


def _escape_bars(line):
    parts = _INLINE_LITERAL.split(line)
    return "".join(p if p.startswith("``") else p.replace("|", r"\|") for p in parts)


def _indent(line):
    return len(line) - len(line.lstrip())


def _clean_docstring(app, what, name, obj, options, lines):
    # 1) module docstrings: a paragraph followed by an indented block -> "::"
    if what == "module":
        for i in range(len(lines) - 2):
            text, blank, nxt = lines[i], lines[i + 1], lines[i + 2]
            if (text.strip() and not blank.strip() and nxt.strip()
                    and _indent(nxt) > _indent(text) and not text.rstrip().endswith("::")):
                lines[i] = text.rstrip() + (":" if text.rstrip().endswith(":") else "::")
    # 2) escape "|" everywhere except in literal blocks and ``inline literals``
    literal_indent = None
    for i, line in enumerate(lines):
        if literal_indent is not None:
            if not line.strip() or _indent(line) > literal_indent:
                continue
            literal_indent = None
        if line.rstrip().endswith("::"):
            literal_indent = _indent(line)
        lines[i] = _escape_bars(line)


def setup(app):
    app.connect("autodoc-process-docstring", _clean_docstring, priority=600)
