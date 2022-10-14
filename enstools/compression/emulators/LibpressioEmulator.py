"""
Definition of the class LibpressioEmulator: an Emulator that uses Libpressio.
"""


import numpy as np

from enstools.encoding.api import Compressors, CompressionModes, compression_mode_aliases
from enstools.compression.emulators.EmulatorClass import Emulator


class LibpressioEmulator(Emulator):
    def __init__(self, compressor_name: Compressors, mode: CompressionModes, parameter: float, uncompressed_data: np.ndarray):
        try:
            from libpressio import PressioCompressor
        except ModuleNotFoundError as err:
            print(
                "The library libpressio its not available, can not proceed with analysis.")
            raise err
        self._config = compressor_configuration(
            compressor_name, mode, parameter, uncompressed_data)
        self.compressor = PressioCompressor.from_config(self._config)

    def compress(self, uncompressed_data: np.array) -> np.array:
        self._shape = uncompressed_data.shape
        self._dtype = uncompressed_data.dtype
        return self.compressor.encode(uncompressed_data)

    def decompress(self, compressed_data: np.array) -> np.array:
        decompressed = np.zeros(shape=self._shape, dtype=self._dtype)
        decompressed = self.compressor.decode(compressed_data, decompressed)
        return decompressed

    def compress_and_decompress(self, uncompressed_data: np.array) -> np.array:
        compressed_data = self.compress(uncompressed_data=uncompressed_data)
        return self.decompress(compressed_data=compressed_data)

    def compression_ratio(self):
        metrics = self.compressor.get_metrics()
        return metrics['size:compression_ratio']


def compressor_configuration(compressor: Compressors, mode: CompressionModes, parameter: float,
                             data: np.ndarray):
    compressor_ids = {Compressors.SZ: "sz", Compressors.ZFP: "zfp"}
    if compressor == Compressors.SZ:
        compressor_config = {
            "sz:error_bound_mode_str": compression_mode_aliases[mode],
            "sz:abs_err_bound": parameter,
            "sz:rel_err_bound": parameter,
            "sz:pw_rel_err_bound": parameter,
            "sz:metric": "size",
        }
    elif compressor == Compressors.ZFP:
        compressor_config = {
            f"zfp:{compression_mode_aliases[mode]}": parameter,
            "zfp:type": 3 if data.dtype == np.float32 else 4,
            "zfp:dims": len(data.shape),
            "zfp:wra": 0,
            "zfp:execution_name": "serial",
            "zfp:metric": "size",
        }
    else:
        raise NotImplementedError(
            f"{compressor} {compression_mode_aliases[mode]}")
    return {
        "compressor_id": compressor_ids[compressor],
        "compressor_config": compressor_config,
    }
