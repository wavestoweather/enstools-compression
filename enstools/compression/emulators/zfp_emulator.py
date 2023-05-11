"""
Definition of the class ZFPEmulator: an Emulator that uses ZFP.
Can only work with the ZFP compressor.
"""
from sys import getsizeof

import numpy as np
import zfpy

from enstools.compression.emulators.emulator_class import Emulator
from enstools.core.errors import EnstoolsError


from enstools.encoding.variable_encoding import Encoding, LossyEncoding


class ZFPEmulator(Emulator):
    """
    Emulator class that relies on the zfpy library to compress the data.
    Only usable for zfp compressor.
    """
    # pylint: disable=c-extension-no-member
    def __init__(self, specification: Encoding, uncompressed_data: np.ndarray):
        if not isinstance(specification, LossyEncoding):
            raise EnstoolsError("Our current implementation of ZFPEmulator only covers the lossy compressor ZFP.")

        compressor_name = specification.compressor
        mode = specification.mode
        parameter = specification.parameter

        if compressor_name != "zfp":
            raise EnstoolsError(f"Trying to use ZFP analysis compressor for compressor {compressor_name}")

        if mode == "accuracy":
            mode = "tolerance"
        self.parameters = {mode: parameter}
        self._compression_ratio = None

    def compress(self, uncompressed_data: np.ndarray) -> np.ndarray:
        """
        Compress the uncompressed data.

        Args:
            uncompressed_data (np.ndarray): The uncompressed data.

        Returns:
            np.ndarray: The compressed data.
        """

        # Compress the data
        compressed_data = zfpy.compress_numpy(uncompressed_data, **self.parameters)

        # Get compression ratio
        compressed_size = getsizeof(compressed_data)
        original_size = uncompressed_data.size * uncompressed_data.itemsize
        compression_ratio = original_size / compressed_size
        # Store compression ratio
        self._compression_ratio = compression_ratio
        # Return compressed data
        return compressed_data

    def decompress(self, compressed_data: np.ndarray) -> np.ndarray:
        """
        Decompress the compressed data.

        Args:
            compressed_data (np.ndarray): The compressed data.

        Returns:
            np.ndarray: The decompressed data.
        """

        return zfpy.decompress_numpy(compressed_data)

    def compress_and_decompress(self, uncompressed_data: np.ndarray) -> np.ndarray:
        """
        Compress and decompress the data.

        Args:
            uncompressed_data (np.ndarray): The uncompressed data.

        Returns:
            np.ndarray: The decompressed data.
        """

        compressed_data = self.compress(uncompressed_data=uncompressed_data)
        return self.decompress(compressed_data=compressed_data)

    def compression_ratio(self):
        """
        Get the compression ratio.

        Returns:
            float: The compression ratio.
        """
        return self._compression_ratio
