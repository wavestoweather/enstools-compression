Basic Examples
==============



Save a dataset into a compressed file
-------------------------------------

Once **enstools-compression** has been installed, **enstools.io.write** accepts the compression parameter that allows us
to compress our files apply lossless or lossy methods.

An example with lossless compression:

.. code::

    write(dataset, "output.nc", compression="lossless")

An example with lossy compression:

.. code::

    write(dataset, "output.nc", compression="lossy,zfp,rate,3.2")


Compress existing file
----------------------

Using the **Command Line Interface** it is very easy to compress existing files as well:

An example with lossless compression:
    >>> enstools-compression "input.nc" -o "output.nc" --compression "lossless"

An example with lossy compression:
    >>> enstools-compression "input.nc" -o "output.nc" --compression "lossy,sz,rel,1e-5"


More examples:
--------------

Explore the :ref:`Examples` section to see **more examples** on all the other features!
