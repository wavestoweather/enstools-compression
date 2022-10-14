from enstools.encoding.api import Compressors, CompressionModes, check_sz_availability, check_libpressio_availability
from utils import TestClass
import numpy as np

import pytest



class TestEmulators:
    def test_ZFPEmulator(self):
        from enstools.compression.emulators import ZFPEmulator
        settings = {
            "compressor_name": Compressors.ZFP,
            "mode": CompressionModes.RATE,
            "parameter": 3.2,
        }
        data_size = (100, 100)
        data = np.random.random(data_size)
        analysis_compressor = ZFPEmulator(**settings, uncompressed_data=data)

        recovered_data = analysis_compressor.compress_and_decompress(data)
        print(f"Compression Ratio:{analysis_compressor.compression_ratio():.2f}")

    @pytest.mark.skipif(not check_libpressio_availability(), reason="Requires LibPressio")
    def test_LibpressioEmulator(self):
        from enstools.compression.emulators import LibpressioEmulator

        settings = {
            "compressor_name": Compressors.ZFP,
            "mode": CompressionModes.RATE,
            "parameter": 3.2,
        }
        data_size = (100, 100)
        data = np.random.random(data_size)
        analysis_compressor = LibpressioEmulator(**settings, uncompressed_data=data)

        recovered_data = analysis_compressor.compress_and_decompress(data)
        print(f"Compression Ratio:{analysis_compressor.compression_ratio():.2f}")

    def test_FilterAnalysisCompressor(self):
        import hdf5plugin
        from enstools.compression.emulators import FilterEmulator
        settings = {
            "compressor_name": Compressors.ZFP,
            "mode": CompressionModes.RATE,
            "parameter": 3.2,
        }
        data_size = (100, 100)
        data = np.random.random(data_size)
        analysis_compressor = FilterEmulator(**settings, uncompressed_data=data)

        recovered_data = analysis_compressor.compress_and_decompress(data)
        print(f"Compression Ratio:{analysis_compressor.compression_ratio():.2f}")

    @pytest.mark.skipif(not check_sz_availability(), reason="Requires SZ filter.")
    def test_FilterAnalysisCompressor_with_SZ(self):
        from enstools.compression.emulators import FilterEmulator
        settings = {
            "compressor_name": Compressors.SZ,
            "mode": CompressionModes.REL,
            "parameter": 0.001,
        }
        data_size = (100, 100)
        data = np.random.random(data_size)
        analysis_compressor = FilterEmulator(**settings, uncompressed_data=data)

        recovered_data = analysis_compressor.compress_and_decompress(data)
        print(f"Compression Ratio:{analysis_compressor.compression_ratio():.2f}")


class TestEmulate(TestClass):
    def test_emulation(self):
        from enstools.io import read
        from enstools.compression.emulation import emulate_compression_on_dataset
        input_tempdir = self.input_directory_path
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(3, 4)]
        compression_specifications = ["lossy,zfp,rate,1.0"]

        for ds in datasets:
            input_path = input_tempdir / ds
            # Import and launch compress function
            ds = read(input_path)
            for compression_specification in compression_specifications:
                ds, _ = emulate_compression_on_dataset(ds, compression=compression_specification)

    @pytest.mark.skipif(not check_sz_availability(), reason="Requires SZ filter.")
    def test_emulation_with_sz(self):
        from enstools.io import read
        from enstools.compression.emulation import emulate_compression_on_dataset
        input_tempdir = self.input_directory_path
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(3, 4)]
        compression_specifications = [
            "lossy,sz,rel,0.1",
            "lossy,sz,pw_rel,0.01",
        ]

        for ds in datasets:
            input_path = input_tempdir / ds
            # Import and launch compress function
            ds = read(input_path)
            for compression_specification in compression_specifications:
                ds, _ = emulate_compression_on_dataset(ds, compression=compression_specification)
