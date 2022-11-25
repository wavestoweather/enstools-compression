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


Compress an existing file
----------------------

Using the **Command Line Interface** it is very easy to compress existing files as well:

An example with lossless compression:
    >>> enstools-compression "input.nc" -o "output.nc" --compression "lossless"

An example with lossy compression:
    >>> enstools-compression "input.nc" -o "output.nc" --compression "lossy,sz,rel,1e-5"


Analyze a dataset to find compression specifications
-------------------------------------

To find compression specifications, an automatic search function **enstools.compression.analyze_dataset** can be used to find which compression parameters yield the highest compression ratio while keeping certain quality constrains:

.. code::

    specifications, metrics = analyze_dataset(dataset)

By default the constrains used are
    >>> constrains="correlation_I:5,ssim_I:2"

This stands for 5 9s of correlation (0.99999) and 2 9s of structural similarity (0.99).

.. code::

    specifications, metrics = analyze_dataset(dataset, constrains="correlation:0.99999,ssim:0.99")



More examples:
--------------

Explore the :ref:`Examples` section to see **more examples** on all the other features!
