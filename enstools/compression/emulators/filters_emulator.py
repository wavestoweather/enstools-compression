"""
Definition of the class FilterEmulator: an Emulator that uses the hdf5 filters.
"""

import io

import numpy as np
import h5py

from enstools.core.tempdir import TempDir
from enstools.encoding.variable_encoding import Encoding
from .emulator_class import Emulator



# TODO: Patch to make Tempdir usable as a context manager. Shouldn't be necessary in future releases of enstools.


if not hasattr(TempDir, "__enter__"):
    # pylint: disable=unused-argument
    def __enter__(self, parentdir=None, check_free_space=False, cleanup=True):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    TempDir.__enter__ = __enter__
    TempDir.__exit__ = __exit__


class FilterEmulator(Emulator):
    """
    Emulator class that relies on the hdf5 filters to compress the data using a IO file object to do that in memory.
    """

    def __init__(self, specification: Encoding, uncompressed_data: np.ndarray):
        """
        Initialize the FilterEmulator.

        Args:
            specification (Encoding): The encoding specification.
            uncompressed_data (np.ndarray): The uncompressed data.
        """

        self.compression = specification

        self._compression_ratio = None

    def compress(self, uncompressed_data: np.ndarray) -> np.ndarray:
        """
        FilterEmulator doesn't have the compress method implemented.
        Use directly compress_and_decompress.

        """

        raise NotImplementedError

    def decompress(self, compressed_data: np.ndarray) -> np.ndarray:
        """
        FilterEmulator doesn't have the decompress method implemented.
        Use directly compress_and_decompress.

        """

        raise NotImplementedError

    def compress_and_decompress(self, uncompressed_data: np.ndarray) -> np.ndarray:
        """
        Compress and decompress the data.

        Args:
            uncompressed_data (np.ndarray): The uncompressed data.

        Returns:
            np.ndarray: The decompressed data.
        """

        # Create a temporary directory in the system memory

        dummy_var = "tmp"

        # Calculate uncompressed size
        uncompressed_size = uncompressed_data.dtype.itemsize * uncompressed_data.size

        # If the key "chunksizes" is inside the encoding, we need to rename it.
        encoding = dict(self.compression)
        if "chunksizes" in encoding:
            encoding["chunks"] = encoding.pop("chunksizes")

        # Initialize file object
        with io.BytesIO() as bio:

            # Compress data
            with h5py.File(bio, mode='w') as temporary_file:
                temporary_file.create_dataset(dummy_var, data=uncompressed_data, **encoding)

            # Get compressed file
            compressed_size = bio.getbuffer().nbytes

            # Decompress data
            with h5py.File(bio, mode="r") as temporary_file:
                recovered_data = temporary_file[dummy_var][()]

            # Save compression ratio
            self._compression_ratio = uncompressed_size / compressed_size

            # Return the recovered data
            return recovered_data

    def compression_ratio(self):
        """
        Get the compression ratio.

        Returns:
            float: The compression ratio.
        """
        return self._compression_ratio
