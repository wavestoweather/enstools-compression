.. _UsingAPI:

Using the Python API
--------------------

Writing compressed files
........................

Using enstools's **read** and **write** compressing a file could be done by:

.. code::

    from enstools.io import read,write

    with read("input.nc") as dataset:
        write(dataset,"output.nc", compression="lossless")

We added a method that does just thad adding few more features: :meth:`enstools.compression.api.compress`




Finding compression parameters
..............................


:meth:`enstools.compression.api.analyze_files`
:meth:`enstools.compression.api.analyze_dataset`

To analyze a dataset:

.. code::

    from enstools.io import read
    from enstools.encoding.api import analyze_dataset

    with read("input.nc") as dataset:
        results = analyze_dataset(dataset)

It is possible to use different constrains:

.. code::

    from enstools.io import read
    from enstools.encoding.api import analyze_dataset

    with read("input.nc") as dataset:
        results = analyze_dataset(dataset, constrains="correlation_I:7,ssim_I:5)


To analyze a file:

.. code::

    from enstools.encoding.api import analyze_files

    results = analyze_files("input.nc")



