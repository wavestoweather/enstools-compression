from abc import ABC, abstractmethod
import numpy as np

from enstools.encoding import Compressors, CompressionModes


class AnalysisCompressor(ABC):
    @abstractmethod
    def __init__(self, compressor_name: Compressors, mode: CompressionModes, parameter: float, uncompressed_data: np.ndarray):
        """Init method requires certain parameters"""

    @abstractmethod
    def compress(self, uncompressed_data: np.array) -> np.array:
        """Compress method gets a numpy array and returns a numpy array"""

    @abstractmethod
    def decompress(self, compressed_data: np.array) -> np.array:
        """Decompress method gets a numpy array and returns a numpy array"""

    @abstractmethod
    def compression_ratio(self) -> float:
        """compression_ratio method returns the compression ratio achieved during compression"""
