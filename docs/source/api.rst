Python API
===============================================

..
   This are the things that are made accessible through the api.py file:
   from .pruner import pruner
   from .compressor import compress
   from .analyzer.analyzer import analyze_files, analyze_dataset
   from .significant_bits import analyze_file_significant_bits
   from .evaluator import evaluate
   from .emulation import emulate_compression_on_dataset, emulate_compression_on_data_array,\
      emulate_compression_on_numpy_array


File Compression
----------------

.. autosummary::
   :toctree: compress_files

    enstools.compression.api.compress

Analysis
--------

.. autosummary::
   :toctree: analyze

    enstools.compression.api.analyze_dataset
    enstools.compression.api.analyze_files

Significant Bits
----------------
.. autosummary::
   :toctree: significant_bits

    enstools.compression.api.analyze_file_significant_bits

Pruner
----------------
.. autosummary::
   :toctree: pruner

    enstools.compression.api.pruner



Emulation
---------
.. autosummary::
   :toctree: emulation

    enstools.compression.api.emulate_compression_on_dataset
    enstools.compression.api.emulate_compression_on_data_array
    enstools.compression.api.emulate_compression_on_numpy_array

Evaluation
---------
.. autosummary::
   :toctree: evaluate

    enstools.compression.api.evaluate
    

