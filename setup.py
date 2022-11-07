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

def find_enstools_packages():
    """
    Find the packages inside the enstools folder.
    """

    return [f'enstools.{p}' for p in (find_packages(f'{os.path.dirname(__file__)}/enstools'))]


# perform the actual install operation
setup(name="enstools-compression",
      version="0.1.8",
      author="Oriol Tintó",
      author_email="oriol.tinto@lmu.de",
      long_description=long_description,
      long_description_content_type='text/markdown',
      url="https://github.com/wavestoweather/enstools-compression",

      packages=find_enstools_packages(),

      install_requires=[
          "enstools>=2022.9.3",
          "enstools-encoding>=0.1.9",
          "zfpy",
      ],
      entry_points={
          'console_scripts': [
              'enstools-compression=enstools.compression.cli:main'
          ],
      },
      )
