Examples
========

Simplest case
-------------

Once **enstools-compression** has been installed, **enstools.io.write** accepts the compression parameter that allows us
to compress our files apply lossless or lossy methods.

An example with lossless compression:

.. code::

    write(dataset, "output.nc", compression="lossless")

An example with lossy compression:

.. code::

    write(dataset, "output.nc", compression="lossy,zfp,rate,3.2")

.. warning::
    This documentation is incomplete.
