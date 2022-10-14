from os.path import isfile, join

import pytest

from enstools.encoding.api import check_sz_availability

from utils import file_size, wrapper, TestClass

folders = None


class TestCompressor(TestClass):
    def test_dataset_exists(self):
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            assert (self.input_directory_path / ds).exists()

    def test_compress_vanilla(self):
        wrapper(self)

    def test_compress_json_parameters(self):
        import json

        compression_parameters = {"default": "lossless",
                                  "temperature": "lossy,zfp,rate,3",
                                  "precipitation": "lossless",
                                  }
        json_file_path = self.input_directory_path /  "compression.json"
        with json_file_path.open("w") as out_file:
            json.dump(compression_parameters, out_file)
        compression = json_file_path
        wrapper(self, compression=compression)

    def test_compress_yaml_parameters(self):
        import yaml

        compression_parameters = {"default": "lossless",
                                  "temperature": "lossy,zfp,rate,3",
                                  "precipitation": "lossless",
                                  }
        yaml_file_path = self.input_directory_path / "compression.yaml"

        with yaml_file_path.open("w") as out_file:
            yaml.dump(compression_parameters, out_file)
        compression = yaml_file_path
        wrapper(self, compression=compression)

    def test_compress_auto(self):
        compression = "auto"
        wrapper(self, compression=compression)

    def test_compress_ratios_lossy(self):
        from enstools.compression.api import compress
        # Check that compression works when specifying compression = lossy:sz
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(2, 4)]
        compression = "lossy,zfp,rate,1.0"
        for ds in datasets:
            input_path = self.input_directory_path / ds

            output_file_path = self.output_directory_path / ds
            compress(input_path, output_file_path, compression=compression, nodes=0)
            initial_size = file_size(input_path)
            final_size = file_size(output_file_path)
            assert initial_size > final_size

    def test_compress_ratios_lossless(self):
        from enstools.compression.api import compress
        # Check that compression works when specifying compression = lossy:sz
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(2, 4)]
        compression = "lossless"
        for ds in datasets:
            input_path = self.input_directory_path / ds
            output_file_path = self.output_directory_path / ds
            compress(input_path, output_file_path, compression=compression, nodes=0)
            initial_size = file_size(input_path)
            final_size = file_size(output_file_path)
            assert initial_size > final_size

    @pytest.mark.skipif(not check_sz_availability(), reason="Requires SZ")
    def test_filters_availability(self):
        from enstools.encoding.api import check_filters_availability
        assert check_filters_availability()

    def test_blosc_filter_availability(self):
        from enstools.encoding.api import check_blosc_availability
        assert check_blosc_availability

    def test_specify_single_file_output_name(self):
        from enstools.compression.api import compress
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = self.input_directory_path / ds
            output_filename = self.output_directory_path / f"{ds.replace('.nc', '_output.nc')}"
            # Import and launch compress function
            compress(input_path, output_filename, compression="lossless", nodes=0)

    def test_compress_single_file(self):
        from enstools.compression.api import compress
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = self.input_directory_path / ds
            output_filename = self.output_directory_path / f"{ds.replace('.nc', '_output.nc')}"
            # Import and launch compress function
            compress(input_path, output_filename, compression="lossless", nodes=0)


