# To have the Version number in a single place, there's a VERSION file in the package root directory.
# Here we read that file.
from pathlib import Path
version_file = Path(__file__).resolve().parent.parent.parent / "VERSION"
__version__ = version_file.read_text().strip()

