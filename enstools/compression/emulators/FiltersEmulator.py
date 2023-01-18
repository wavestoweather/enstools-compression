"""
Definition of the class FilterEmulator: an Emulator that uses the hdf5 filters.
"""

import io
from typing import Union

import numpy as np

from .EmulatorClass import Emulator
from enstools.io import write, read
from enstools.core.tempdir import TempDir
from pathlib import Path
from enstools.encoding.api import VariableEncoding
from enstools.encoding.variable_encoding import Encoding
from enstools.compression.size_metrics import file_size

import h5py

# TODO: Patch to make Tempdir usable as a context manager. Shouldn't be necessary in future releases of enstools.


if not hasattr(TempDir, "__enter__"):
    def __enter__(self, parentdir=None, check_free_space=False, cleanup=True):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    TempDir.__enter__ = __enter__
    TempDir.__exit__ = __exit__


class FilterEmulator(Emulator):
    """
    Use the filters to compress the data
    """

    def __init__(self, specification: Encoding, uncompressed_data: np.ndarray):
        self.compression = specification

        self._compression_ratio = None

    def compress(self, uncompressed_data: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def decompress(self, compressed_data: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def compress_and_decompress(self, uncompressed_data: np.ndarray) -> np.ndarray:
        # Create a temporary directory in the system memory
        
        dummy_var = "tmp"

        # Calculate uncompressed size
        uncompressed_size = uncompressed_data.dtype.itemsize * uncompressed_data.size

        # Initialize file object
        with io.BytesIO() as bio:
        
            # Compress data
            with h5py.File(bio, mode='w') as f:
                f.create_dataset(dummy_var, data=uncompressed_data, **self.compression)
            
            # Get compressed file
            compressed_size = bio.getbuffer().nbytes

            # Decompress data
            with h5py.File(bio, mode="r") as f:
                recovered_data = f[dummy_var][()]

            # Save compression ratio
            self._compression_ratio = uncompressed_size / compressed_size

            # Return the recovered data
            return recovered_data

    def compression_ratio(self):
        return self._compression_ratio
