"""
Definition of the class LibpressioEmulator: an Emulator that uses Libpressio.
"""


import numpy as np

from enstools.compression.emulators.emulator_class import Emulator
from enstools.core.errors import EnstoolsError
from enstools.encoding.variable_encoding import Encoding, LossyEncoding


def libpressio_is_available():
    # pylint: disable=import-outside-toplevel, unused-import
    """
    Check if libpressio is available.
        
    Returns:
        bool: True if libpressio is available, False otherwise.
    """

    try:
        from libpressio import PressioCompressor
        return True
    except ModuleNotFoundError:
        return False


class LibpressioEmulator(Emulator):
    """
    Class representing a LibpressioEmulator.

    Args:
        specification (Encoding): The encoding specification.
        uncompressed_data (np.ndarray, optional): The uncompressed data. Defaults to None.
    """

    def __init__(self, specification: Encoding, uncompressed_data: np.ndarray = None):
        """
        Initialize the LibpressioEmulator.

        Args:
            specification (Encoding): The encoding specification.
            uncompressed_data (np.ndarray, optional): The uncompressed data. Defaults to None.

        Raises:
            EnstoolsError: If the specification is not an instance of LossyEncoding.
        """
        # pylint: disable=import-outside-toplevel, import-error

        from libpressio import PressioCompressor
        if not isinstance(specification, LossyEncoding):
            raise EnstoolsError("Our current implementation of Libpressio only covers lossy compressors.")
        compressor_name = specification.compressor
        mode = specification.mode
        parameter = specification.parameter
        self._config = compressor_configuration(
            compressor_name, mode, parameter, uncompressed_data)
        self.compressor = PressioCompressor.from_config(self._config)
        self._shape = None
        self._dtype = None

    def compress(self, uncompressed_data: np.ndarray) -> np.ndarray:
        """
        Compress the uncompressed data.

        Args:
            uncompressed_data (np.ndarray): The uncompressed data.

        Returns:
            np.ndarray: The compressed data.
        """

        self._shape = uncompressed_data.shape
        self._dtype = uncompressed_data.dtype
        return self.compressor.encode(uncompressed_data)

    def decompress(self, compressed_data: np.ndarray) -> np.ndarray:
        """
        Decompress the compressed data.

        Args:
            compressed_data (np.ndarray): The compressed data.

        Returns:
            np.ndarray: The decompressed data.
        """

        decompressed = np.zeros(shape=self._shape, dtype=self._dtype)
        decompressed = self.compressor.decode(compressed_data, decompressed)
        return decompressed

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

        metrics = self.compressor.get_metrics()
        return metrics['size:compression_ratio']


def compressor_configuration(compressor: str, mode: str, parameter: float,
                             data: np.ndarray):
    """
    Generate the compressor configuration.

    Args:
        compressor (str): The name of the compressor.
        mode (str): The mode of the compressor.
        parameter (float): The parameter of the compressor.
        data (np.ndarray): The data.

    Raises:
        NotImplementedError: If the compressor and mode combination is not implemented.
    """

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
