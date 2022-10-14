"""
Definition of the class LibpressioEmulator: an Emulator that uses ZFP.
Can only work with the ZFP compressor.
"""

import numpy as np
from sys import getsizeof
from enstools.compression.emulators.EmulatorClass import Emulator
from enstools.encoding.api import compression_mode_aliases, Compressors
from enstools.core.errors import EnstoolsError
import zfpy


class ZFPEmulator(Emulator):
    def __init__(self, compressor_name, mode, parameter, uncompressed_data):
        mode_str = compression_mode_aliases[mode]
        if compressor_name != "zfp" and compressor_name != Compressors.ZFP:
            raise EnstoolsError(f"Trying to use ZFP analysis compressor for compressor {compressor_name}")
        if mode_str == "accuracy":
            mode_str = "tolerance"
        self.parameters = {mode_str: parameter}
        self._compression_ratio = None

    def compress(self, uncompressed_data: np.array) -> np.array:
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

    def decompress(self, compressed_data: np.array) -> np.array:
        return zfpy.decompress_numpy(compressed_data)

    def compress_and_decompress(self, uncompressed_data: np.array) -> np.array:
        compressed_data = self.compress(uncompressed_data=uncompressed_data)
        return self.decompress(compressed_data=compressed_data)

    def compression_ratio(self):
        return self._compression_ratio
