"""
# to convert enstools into a namespace package, the version is now listed here and not in the level above
import pkg_resources  # part of setuptools

try:
    version = pkg_resources.require("enstools-compression")[0].version
    __version__ = version
except pkg_resources.ContextualVersionConflict:
    __version__ = "99999"

"""
# FIXME: There should be a proper way of doing this. Meanwhile I just keep it without a __version__ variable.