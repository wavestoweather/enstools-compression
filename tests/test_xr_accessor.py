from utils import TestClass

from enstools.compression import xr_accessor # noqa
import enstools.io


class TestXRAccessor(TestClass):
    def test_dataset_compression_call_accessor(self):
        compression = "lossy,zfp,rate,1"
        data_files = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for df in data_files:
            input_path = self.input_directory_path / df
            with enstools.io.read(input_path) as ds:
                ds.compression(compression)

    def test_dataset_compression_emulate_accessor(self):
        compression = "lossy,zfp,rate,1"
        data_files = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for df in data_files:
            input_path = self.input_directory_path / df
            with enstools.io.read(input_path) as ds:
                ds.compression.emulate(compression)

    def test_dataset_compression_analyze_accessor(self):
        data_files = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for df in data_files:
            input_path = self.input_directory_path / df
            with enstools.io.read(input_path) as ds:
                ds.compression.analyze(compressor="zfp", mode="rate")

    def test_dataArray_compression_call_accessor(self):
        compression = "lossy,zfp,rate,1"
        data_files = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for df in data_files:
            input_path = self.input_directory_path / df
            with enstools.io.read(input_path) as ds:
                for da in ds.data_vars:
                    ds[da].compression(compression)

    def test_dataArray_compression_emulate_accessor(self):
        compression = "lossy,zfp,rate,1"
        data_files = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for df in data_files:
            input_path = self.input_directory_path / df
            with enstools.io.read(input_path) as ds:
                for da in ds.data_vars:
                    ds[da].compression.emulate(compression)

    def test_dataArray_compression_analyze_accessor(self):
        data_files = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for df in data_files:
            input_path = self.input_directory_path / df
            with enstools.io.read(input_path) as ds:
                for var in ds.data_vars:
                    ds[var].compression.analyze(compressor="zfp", compression_mode="rate", constrains="correlation_I:5")
