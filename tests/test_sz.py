import numpy as np

from utils import wrapper, TestClass

folders = None


class TestSZ(TestClass):
    def test_sz_analyzer(self):
        from enstools.compression.api import analyze_files
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = self.input_directory_path / ds
            analyze_files(file_paths=input_path, compressor="sz")

    def test_compress_sz_pw_rel(self):
        compression = "lossy,sz,pw_rel,0.001"
        wrapper(self, compression=compression)

    def test_consistency_sz_pw_rel(self):
        import enstools.compression.api
        from enstools.encoding.api import VariableEncoding
        import enstools.io
        tolerance = 0.001
        compression = f"lossy,sz,pw_rel,{tolerance}"
        # Check that the compression without specifying compression parameters works

        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for dataset_name in datasets:
            input_path = self.input_directory_path / dataset_name

            # Check that the output file can be loaded
            with enstools.io.read(input_path) as ds:
                for var in ds.data_vars:
                    data_array = ds[var]
                    encoding = VariableEncoding(specification=compression)
                    compressed_da, _ = enstools.compression.api.emulate_compression_on_data_array(
                        data_array=data_array,
                        compression_specification=encoding,
                        in_place=False,
                    )
                    diff = compressed_da - data_array
                    diff /= data_array

                    assert (np.abs(diff.values) < (data_array.values * tolerance)).all()

    def test_compress_sz_abs(self):
        compression = "lossy,sz,abs,0.01"
        wrapper(self, compression=compression)

    def test_consistency_sz_abs(self):
        import enstools.compression.api
        from enstools.encoding.api import VariableEncoding
        import enstools.io
        tolerance = 0.01
        compression = f"lossy,sz,abs,{tolerance}"
        # Check that the compression without specifying compression parameters works

        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for dataset_name in datasets:
            input_path = self.input_directory_path / dataset_name

            # Check that the output file can be loaded
            with enstools.io.read(input_path) as ds:
                for var in ds.data_vars:
                    data_array = ds[var]
                    encoding = VariableEncoding(specification=compression)
                    compressed_da, _ = enstools.compression.api.emulate_compression_on_data_array(
                        data_array=data_array,
                        compression_specification=encoding,
                        in_place=False,
                    )
                    diff = compressed_da - data_array
                    assert (np.abs(diff.values) < tolerance).all()

    def test_compress_sz_rel(self):
        compression = "lossy,sz,rel,0.001"
        wrapper(self, compression=compression)


    def test_consistency_sz_rel(self):
        import enstools.compression.api
        from enstools.encoding.api import VariableEncoding
        import enstools.io
        tolerance = 0.01
        compression = f"lossy,sz,rel,{tolerance}"
        # Check that the compression without specifying compression parameters works

        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for dataset_name in datasets:
            input_path = self.input_directory_path / dataset_name

            # Check that the output file can be loaded
            with enstools.io.read(input_path) as ds:
                for var in ds.data_vars:
                    data_array = ds[var]
                    encoding = VariableEncoding(specification=compression)
                    compressed_da, _ = enstools.compression.api.emulate_compression_on_data_array(
                        data_array=data_array,
                        compression_specification=encoding,
                        in_place=False,
                    )
                    abs_tolerance = float(data_array.max() - data_array.min()) * tolerance
                    diff = compressed_da - data_array
                    assert (np.abs(diff.values) < abs_tolerance).all()

