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

    def test_dataset_encoding(self):
        data_files = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for df in data_files:
            input_path = self.input_directory_path / df
            with enstools.io.read(input_path) as ds:
                enc = ds.compression.encoding("lossless")

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

    def test_dataArray_encoding(self):
        data_files = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for df in data_files:
            input_path = self.input_directory_path / df
            with enstools.io.read(input_path) as ds:
                for var in ds.data_vars:
                    enc = ds[var].compression.encoding("lossless")

    def test_to_compressed_netcdf(self):
        data_files = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for df in data_files:
            input_path = self.input_directory_path / df
            output_path = self.output_directory_path / df
            with enstools.io.read(input_path) as ds:
                ds.to_compressed_netcdf(output_path, compression="lossy,sz,pw_rel,1e-5")
