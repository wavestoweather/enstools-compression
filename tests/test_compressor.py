from os.path import isfile, join

import pytest

from enstools.encoding import check_sz_availability, check_libpressio_availability

from utils import file_size, wrapper, TestClass

folders = None


class TestCompressor(TestClass):
    def test_dataset_exists(self):
        input_tempdir = self.input_tempdir
        output_tempdir = self.output_tempdir
        tempdir_path = input_tempdir.getpath()

        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            assert isfile(join(tempdir_path, ds))

    def test_analyzer(self):
        from enstools.compression import analyze
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            analyze(file_paths=[input_path])

    def test_zfp_analyzer(self):
        from enstools.compression import analyze
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            analyze(file_paths=[input_path], compressor="zfp")

    def test_inverse_analyzer(self):
        """
        This tests checks that we can find compression parameters to fulfill a certain compression ratio.
        """
        from enstools.compression import analyze
        # The resulting compression ratio should be within this tolerance.
        TOLERANCE = 1
        cr_label = "compression_ratio"
        input_tempdir = self.input_tempdir
        thresholds = {cr_label: 5}
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(2, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            encodings, metrics = analyze(file_paths=[input_path], thresholds=thresholds)
            if not metrics:
                raise AssertionError("Metrics shouldn't be empty")

            for var in metrics:
                if abs(metrics[var][cr_label] - thresholds[cr_label]) > TOLERANCE:
                    raise AssertionError(f"The resulting compression ratio of {metrics[var][cr_label]:.2f}"
                                         f"x is not close enough to the target of {thresholds[cr_label]:.2f}")

    @pytest.mark.skipif(not check_libpressio_availability(), reason="Requires libpressio")
    def test_sz_analyzer(self):
        from enstools.compression import analyze
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            analyze(file_paths=[input_path], compressor="sz")

    def test_compress_vanilla(self):
        wrapper(self)

    def test_compress_json_parameters(self):
        input_tempdir = self.input_tempdir
        import json

        compression_parameters = {"default": "lossless",
                                  "temperature": "lossy,zfp,rate,3",
                                  "precipitation": "lossless",
                                  }
        json_file_path = input_tempdir.getpath() + "/compression.json"
        with open(json_file_path, "w") as out_file:
            json.dump(compression_parameters, out_file)
        compression = json_file_path
        wrapper(self, compression=compression)

    def test_compress_yaml_parameters(self):
        input_tempdir = self.input_tempdir
        import yaml

        compression_parameters = {"default": "lossless",
                                  "temperature": "lossy,zfp,rate,3",
                                  "precipitation": "lossless",
                                  }
        yaml_file_path = input_tempdir.getpath() + "/compression.yaml"
        with open(yaml_file_path, "w") as out_file:
            yaml.dump(compression_parameters, out_file)
        compression = yaml_file_path
        wrapper(self, compression=compression)

    def test_compress_auto(self):
        compression = "auto"
        wrapper(self, compression=compression)

    def test_compress_ratios_lossy(self):
        from enstools.compression import compress
        input_tempdir = self.input_tempdir
        output_tempdir = self.output_tempdir
        # Check that compression works when specifying compression = lossy:sz
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(2, 4)]
        compression = "lossy,zfp,rate,1.0"
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            output_path = output_tempdir.getpath()
            output_file_path = join(output_path, ds)
            compress([input_path], output_path, compression=compression, nodes=0)
            initial_size = file_size(input_path)
            final_size = file_size(output_file_path)
            assert initial_size > final_size

    def test_compress_ratios_lossless(self):
        from enstools.compression import compress
        # Check that compression works when specifying compression = lossy:sz
        input_tempdir = self.input_tempdir
        output_tempdir = self.output_tempdir

        datasets = ["dataset_%iD.nc" % dimension for dimension in range(2, 4)]
        compression = "lossless"
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            output_path = output_tempdir.getpath()
            output_file_path = join(output_path, ds)
            compress([input_path], output_path, compression=compression, nodes=0)
            initial_size = file_size(input_path)
            final_size = file_size(output_file_path)
            assert initial_size > final_size

    @pytest.mark.skipif(not check_sz_availability(), reason="Requires SZ")
    def test_filters_availability(self):
        from enstools.encoding import check_filters_availability
        assert check_filters_availability()

    def test_blosc_filter_availability(self):
        from enstools.encoding import check_blosc_availability
        assert check_blosc_availability

    def test_specify_single_file_output_name(self):
        from enstools.compression import compress
        input_tempdir = self.input_tempdir
        output_tempdir = self.output_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            output_filename = f"{output_tempdir.getpath()}/{ds.replace('.nc', '_output.nc')}"
            # Import and launch compress function
            compress([input_path], output_filename, compression="lossless", nodes=0)

    def test_compress_single_file(self):
        from enstools.compression import compress
        input_tempdir = self.input_tempdir
        output_tempdir = self.output_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            output_filename = f"{output_tempdir.getpath()}/{ds.replace('.nc', '_output.nc')}"
            # Import and launch compress function
            compress(input_path, output_filename, compression="lossless", nodes=0)


