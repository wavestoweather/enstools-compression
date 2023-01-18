"""
Definition of the class LibpressioEmulator: an Emulator that uses Libpressio.
"""


import numpy as np

from enstools.compression.emulators.EmulatorClass import Emulator
from enstools.core.errors import EnstoolsError
from enstools.encoding.variable_encoding import Encoding, LossyEncoding


def libpressio_is_available():
    """
    Check if libpressio is available.
    """
    try:
        from libpressio import PressioCompressor
        return True
    except ModuleNotFoundError:
        return False


class LibpressioEmulator(Emulator):
    def __init__(self, specification: Encoding, uncompressed_data: np.ndarray = None):
        from libpressio import PressioCompressor
        if not isinstance(specification, LossyEncoding):
            raise EnstoolsError("Our current implementation of Libpressio only covers lossy compressors.")
        compressor_name = specification.compressor
        mode = specification.mode
        parameter = specification.parameter
        self._config = compressor_configuration(
            compressor_name, mode, parameter, uncompressed_data)
        self.compressor = PressioCompressor.from_config(self._config)

    def compress(self, uncompressed_data: np.ndarray) -> np.ndarray:
        self._shape = uncompressed_data.shape
        self._dtype = uncompressed_data.dtype
        return self.compressor.encode(uncompressed_data)

    def decompress(self, compressed_data: np.ndarray) -> np.ndarray:
        decompressed = np.zeros(shape=self._shape, dtype=self._dtype)
        decompressed = self.compressor.decode(compressed_data, decompressed)
        return decompressed

    def compress_and_decompress(self, uncompressed_data: np.ndarray) -> np.ndarray:
        compressed_data = self.compress(uncompressed_data=uncompressed_data)
        return self.decompress(compressed_data=compressed_data)

    def compression_ratio(self):
        metrics = self.compressor.get_metrics()
        return metrics['size:compression_ratio']


def compressor_configuration(compressor: str, mode: str, parameter: float,
                             data: np.ndarray):
    if compressor == "sz":
        compressor_config = {
            "sz:error_bound_mode_str": mode,
            "sz:abs_err_bound": parameter,
            "sz:rel_err_bound": parameter,
            "sz:pw_rel_err_bound": parameter,
            "sz:metric": "size",
        }
    elif compressor == "zfp":
        compressor_config = {
            f"zfp:{mode}": parameter,
            "zfp:type": 3 if data.dtype == np.float32 else 4,
            "zfp:dims": len(data.shape),
            "zfp:wra": 0,
            "zfp:execution_name": "serial",
            "zfp:metric": "size",
        }
    else:
        raise NotImplementedError(
            f"{compressor} {mode}")
    return {
        "compressor_id": compressor,
        "compressor_config": compressor_config,
    }
