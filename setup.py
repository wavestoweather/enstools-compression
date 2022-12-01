"""
Setup file for enstools-compression
"""
from setuptools import setup, find_packages
import os.path

# Use the Readme file as long description.
try:
    with open("README.md", "r") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = ""


def get_version():
    from pathlib import Path
    version_path = Path(__file__).parent / "VERSION"
    with version_path.open() as version_file:
        return version_file.read().strip()


def find_enstools_packages():
    """
    Find the packages inside the enstools folder.
    """

    return [f'enstools.{p}' for p in (find_packages(f'{os.path.dirname(__file__)}/enstools'))]


# perform the actual install operation
setup(name="enstools-compression",
      version=get_version(),
      author="Oriol Tintó",
      author_email="oriol.tinto@lmu.de",
      long_description=long_description,
      long_description_content_type='text/markdown',
      url="https://github.com/wavestoweather/enstools-compression",

      packages=find_enstools_packages(),

      install_requires=[
          "enstools>=2022.11.1",
          "enstools-encoding>=2022.11.1",
          "zfpy",
          "hdf5plugin>=4.0.0",
      ],
      entry_points={
          'console_scripts': [
              'enstools-compression=enstools.compression.cli:main'
          ],
      },
      )
