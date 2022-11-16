# to convert enstools into a namespace package, the version is now listed here and not in the level above
import pkg_resources  # part of setuptools
version = pkg_resources.require("enstools-compression")[0].version
__version__ = version
