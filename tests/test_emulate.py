from enstools.compression.emulators.LibpressioEmulator import libpressio_is_available
from enstools.encoding.api import VariableEncoding
from utils import TestClass
import numpy as np

import pytest


class TestEmulators:
    def test_ZFPEmulator(self):
        from enstools.compression.emulators import ZFPEmulator
        settings = {
            "compressor": "zfp",
            "mode": "rate",
            "parameter": 3.2,
        }

        encoding = VariableEncoding(**settings)
        data_size = (100, 100)
        data = np.random.random(data_size)
        analysis_compressor = ZFPEmulator(encoding, uncompressed_data=data)

        recovered_data = analysis_compressor.compress_and_decompress(data)
        print(f"Compression Ratio:{analysis_compressor.compression_ratio():.2f}")

    @pytest.mark.skipif(not libpressio_is_available(), reason="Requires LibPressio")
    def test_LibpressioEmulator(self):
        from enstools.compression.emulators import LibpressioEmulator

        settings = {
            "compressor": "zfp",
            "mode": "rate",
            "parameter": 3.2,
        }
        data_size = (100, 100)
        data = np.random.random(data_size)
        encoding = VariableEncoding(**settings)
        analysis_compressor = LibpressioEmulator(encoding, uncompressed_data=data)

        _ = analysis_compressor.compress_and_decompress(data)
        print(f"Compression Ratio:{analysis_compressor.compression_ratio():.2f}")

    def test_FilterEmulator(self):
        from enstools.compression.emulators import FilterEmulator
        settings = {
            "compressor": "zfp",
            "mode": "rate",
            "parameter": 3.2,
        }
        data_size = (100, 100)
        data = np.random.random(data_size)

        encoding = VariableEncoding(**settings)
        analysis_compressor = FilterEmulator(encoding, uncompressed_data=data)

        _ = analysis_compressor.compress_and_decompress(data)
        print(f"Compression Ratio:{analysis_compressor.compression_ratio():.2f}")

    def test_FilterEmulator_lossless(self):
        from enstools.compression.emulators import FilterEmulator
        data_size = (1000, 1000)
        data = np.sort(np.float32(np.random.randint(0, 10, size=data_size)))

        encoding = VariableEncoding("lossless")

        analysis_compressor = FilterEmulator(encoding, uncompressed_data=data)

        _ = analysis_compressor.compress_and_decompress(data)
        print(f"Compression Ratio:{analysis_compressor.compression_ratio():.2f}")

    def test_FilterAnalysisCompressor_with_SZ(self):
        from enstools.compression.emulators import FilterEmulator
        settings = {
            "compressor": "sz",
            "mode": "rel",
            "parameter": 0.001,
        }
        data_size = (100, 100)
        data = np.random.random(data_size)

        encoding = VariableEncoding(**settings)
        analysis_compressor = FilterEmulator(encoding, uncompressed_data=data)

        _ = analysis_compressor.compress_and_decompress(data)
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

    def test_emulation_consistency(self):
        """
        Test that using the emulator and actually saving the compressed file yield the same results.

        Returns
        -------

        """
        from enstools.compression.api import emulate_compression_on_dataset
        import enstools.io
        
        # Emulator case
        input_tempdir = self.input_directory_path
        output_tempdir = self.output_directory_path
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(3, 4)]
        compression_specifications = [
            "lossy,sz,abs,0.1",
            "lossy,sz,rel,0.1",
            "lossy,sz,pw_rel,0.01",
            "lossy,zfp,accuracy,0.01",
            "lossy,zfp,rate,3.2",
            "lossy,zfp,precision,12",
        ]

        for ds_name in datasets:
            input_path = input_tempdir / ds_name
            output_path = output_tempdir / ds_name
            # Import and launch compress function
            with enstools.io.read(input_path) as ds:
                for compression_specification in compression_specifications:
                    # Save the dataset compressed
                    enstools.io.write(ds=ds, file_path=output_path, compression=compression_specification)

                    # Reload the compressed dataset
                    with enstools.io.read(output_path) as compressed_ds:
                        # Emulate
                        emulated_ds, _ = emulate_compression_on_dataset(ds,
                                                                        compression=compression_specification,
                                                                        in_place=False,
                                                                        )
                        for variable in ds.data_vars:
                            if not np.allclose(compressed_ds[variable], emulated_ds[variable]):
                                raise AssertionError(f"{ds_name=} {variable=} {compression_specification=}")

