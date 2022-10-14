"""
Abstract class which defines the methods that the emulators need to have.
"""

from abc import ABC, abstractmethod
import numpy as np

from enstools.encoding.api import Compressors, CompressionModes


class Emulator(ABC):
    """
    This class provides an emulator.
    The emulator is initialized with a compression specification (compressor_name, mode and parameter)
    and has a method to compress_and_decompress the data.

    Its is useful to evaluate the errors that are introduced by the compression.
    """
    @abstractmethod
    def __init__(self, compressor_name: Compressors, mode: CompressionModes, parameter: float, uncompressed_data: np.ndarray):
        """Init method requires certain parameters"""


    @abstractmethod
    def compress_and_decompress(self, uncompressed_data: np.array) -> np.array:
        """
        Gets a numpy array and returns the same array after compression and deflation .
        Parameters
        ----------
        uncompressed_data: numpy array

        Returns
        -------
        decompressed_data: numpy array
        """

    @abstractmethod
    def compression_ratio(self) -> float:
        """compression_ratio method returns the compression ratio achieved during compression"""
