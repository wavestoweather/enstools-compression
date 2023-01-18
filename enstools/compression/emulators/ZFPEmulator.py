"""
Definition of the class ZFPEmulator: an Emulator that uses ZFP.
Can only work with the ZFP compressor.
"""

import numpy as np
from sys import getsizeof
from enstools.compression.emulators.EmulatorClass import Emulator
from enstools.core.errors import EnstoolsError
import zfpy

from enstools.encoding.variable_encoding import Encoding, LossyEncoding


class ZFPEmulator(Emulator):
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
        return zfpy.decompress_numpy(compressed_data)

    def compress_and_decompress(self, uncompressed_data: np.ndarray) -> np.ndarray:
        compressed_data = self.compress(uncompressed_data=uncompressed_data)
        return self.decompress(compressed_data=compressed_data)

    def compression_ratio(self):
        return self._compression_ratio
