# enstools-compression [![Documentation Status](https://readthedocs.org/projects/enstools/badge/?version=latest)](https://enstools-compression.readthedocs.io/en/latest/?badge=latest)


This package extends [enstools](github.com/wavestoweather/enstools) to enable **lossy** and **lossless** compression 
by using **HDF5 filters**.

Also, it contains a set of tools to help to find appropriate compression specifications.
It includes a **Command Line Interface** to access its features from the command line

For example:
```bash
enstools-compression compress "input.nc" -o "output.nc" --compression "lossless"
```

It has been developed under the [Waves to Weather - Transregional Collaborative Research 
Project (SFB/TRR165)](https://wavestoweather.de). 

# Installation

`pip` is the easiest way to install `enstools-compression` along with all dependencies.

    pip install enstools-compression


# Documentation

Explore [our documentation](https://enstools-compression.readthedocs.io).          

# Acknowledgment and license

Ensemble Tools (`enstools`) is a collaborative development within
Waves to Weather (SFB/TRR165) coordinated by the subproject 
[Z2](https://www.wavestoweather.de/research_areas/phase2/z2) and funded by the
German Research Foundation (DFG).

A full list of code contributors can [CONTRIBUTORS.md](./CONTRIBUTORS.md).

The code is released under an [Apache-2.0 licence](./LICENSE).
