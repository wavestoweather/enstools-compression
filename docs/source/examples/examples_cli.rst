.. _ExamplesCLI:

Command Line Interface examples
--------------------------------

Compressing files
........................

When compressing a single file it is possible to specify the name of the output file or the name of a directory:

.. code::

    enstools-compression compress "input.nc" -o "output.nc" --compression "lossless"

When compressing multiple files it is necessary to specify a folder as an output:

.. code::

    enstools-compression compress "input_1.nc" "input_2.nc" -o "./output_folder/" --compression "lossless"
    enstools-compression compress "input_*.nc" -o "./output_folder/" --compression "lossy,sz,abs,0.01"



Finding compression parameters
..............................

To analyze a file:

.. code::

    enstools-compression analyze "input.nc"


More details:
.............

Take a look into :ref:`CLI` for more details about how the Command Line Interface works.