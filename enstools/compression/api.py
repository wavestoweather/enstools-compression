"""
This module provides a convenient and centralized access point for various functions
from different modules.

By using this API, users can easily access and utilize these functions without needing
to import each module individually.
"""
# pylint: disable=unused-import
from .pruner import pruner
from .compressor import compress
from .analyzer.analyzer import analyze_files, analyze_dataset
from .significant_bits import analyze_file_significant_bits
from .evaluator import evaluate
from .emulation import emulate_compression_on_dataset, emulate_compression_on_data_array,\
    emulate_compression_on_numpy_array
