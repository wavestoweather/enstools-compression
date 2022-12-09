# Configuration file for the Sphinx documentation builder.

# -- Project information

project = 'enstools-compression'
copyright = '2022'
author = 'Oriol Tintó Prims'


def get_version():
    from pathlib import Path
    version_path = Path(__file__).parent.parent.parent / "VERSION"
    with version_path.open() as version_file:
        return version_file.read().strip()


version = get_version()
release = version
# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinxcontrib.autoprogram',
    'sphinx_design',
    'numpydoc',
    'sphinx_copybutton',
    'nbsphinx',
    'nbsphinx_link',
    'IPython.sphinxext.ipython_console_highlighting'
]

exclude_patterns = ['_build', '**.ipynb_checkpoints']


# Flag to allow errors in the nbsphinx thingy
nbsphinx_allow_errors = True

# Set the kernel
nbsphinx_kernel_name = 'python3'



intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'

