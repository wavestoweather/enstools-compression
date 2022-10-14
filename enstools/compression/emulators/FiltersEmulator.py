"""
Definition of the class FilterEmulator: an Emulator that uses the hdf5 filters.
"""

import numpy as np

from enstools.encoding.api import Compressors, CompressionModes
from .EmulatorClass import Emulator
from enstools.io import write, read
from enstools.core.tempdir import TempDir
import xarray
from pathlib import Path
from enstools.encoding.api import FilterEncodingForH5py
from enstools.compression.size_metrics import file_size

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

    def __init__(self, compressor_name: Compressors, mode: CompressionModes, parameter: float,
                 uncompressed_data: np.ndarray):
        self.compression = FilterEncodingForH5py(compressor=compressor_name, mode=mode, parameter=parameter)

        self._compression_ratio = None

    def compress(self, uncompressed_data: np.array) -> np.array:
        raise NotImplementedError

    def decompress(self, compressed_data: np.array) -> np.array:
        raise NotImplementedError

    def compress_and_decompress(self, uncompressed_data: np.array) -> np.array:
        with TempDir(parentdir="/dev/shm", check_free_space=False) as tempdir:
            tmp_dir_path = Path(tempdir.getpath())
            tmp_file_path = tmp_dir_path / "temp_file.nc"
            tmp_var_name = "tmp"
            dataArray = xarray.DataArray(data=uncompressed_data)
            dataSet = dataArray.to_dataset(name=tmp_var_name)

            # Write the data in an uncompressed file:
            write(dataSet, file_path=tmp_file_path, compression=None)
            uncompressed_size = file_size(tmp_file_path)

            # Write compressed file
            write(dataSet, file_path=tmp_file_path, compression=self.compression.to_string())
            compressed_size = file_size(tmp_file_path)

            # Save compression ratio
            self._compression_ratio = uncompressed_size / compressed_size

            # Read the file again
            recovered_dataSet = read(tmp_file_path)
            recovered_data = recovered_dataSet[tmp_var_name].values

            return recovered_data

    def compression_ratio(self):
        return self._compression_ratio
