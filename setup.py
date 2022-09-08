"""
Setup file for easycompression
"""
from setuptools import setup

# perform the actual install operation
setup(name="enstools-compression",
      version="0.1.0",
      author="Oriol Tintó",
      author_email="oriol.tinto@lmu.de",
      packages=[f"enstools.compression"],
      namespace_packages=['enstools'],

      install_requires=[
          "enstools @ git+https://gitlab.physik.uni-muenchen.de/w2w/enstools.git@compression",
          "enstools-encoding @ git+https://gitlab.physik.uni-muenchen.de/w2w/enstools-encoding.git"
          "zfpy",
      ],
      )
