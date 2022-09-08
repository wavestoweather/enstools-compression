from os.path import isfile, join

import pytest

from enstools.core.errors import EnstoolsError, WrongCompressionModeError
from enstools.encoding import check_sz_availability, check_libpressio_availability


def create_synthetic_dataset(directory):
    """
    Creates three synthetic netcdf datasets (1d,2d,3d) into the provided directory.
    :param directory:
    :return: None
    """
    import numpy as np
    import xarray as xr
    import pandas as pd
    from scipy.ndimage import gaussian_filter
    # Create synthetic datasets
    nx, ny, nz, t = 360, 91, 31, 10
    lon = np.linspace(-180, 180, nx)
    lat = np.linspace(-90, 90, ny)
    levels = np.array(range(nz))
    for dimension in [1, 2, 3]:
        if dimension == 1:
            data_size = (t, nx)
            var_dimensions = ["time", "lon"]
        elif dimension == 2:
            data_size = (t, nx, ny)
            var_dimensions = ["time", "lon", "lat"]
        elif dimension == 3:
            data_size = (t, nz, nx, ny)
            var_dimensions = ["time", "level", "lon", "lat"]
        else:
            raise NotImplementedError()

        temp = 15 + 8 * np.random.randn(*data_size)
        temp = gaussian_filter(temp, sigma=5)
        precip = np.float32(10 * np.random.rand(*data_size))
        precip = gaussian_filter(precip, sigma=5)

        ds = xr.Dataset(
            {
                "temperature": (var_dimensions, temp),
                "precipitation": (var_dimensions, precip),
            },

            coords={
                "lon": lon,
                "lat": lat,
                "level": levels,
                "time": pd.date_range("2014-09-06", periods=t),
                "reference_time": pd.Timestamp("2014-09-05"),
            },
        )
        ds_name = "dataset_%iD.nc" % dimension
        ds.to_netcdf(join(directory, ds_name))


def file_size(file_path):
    from pathlib import Path
    return Path(file_path).stat().st_size


folders = None


def wrapper(cls, compression=None):
    import enstools.io
    input_tempdir = cls.input_tempdir
    output_tempdir = cls.output_tempdir
    # Check that the compression without specifying compression parameters works
    datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
    for ds in datasets:
        input_path = join(input_tempdir.getpath(), ds)
        output_path = output_tempdir.getpath()
        # Import and launch compress function
        enstools.io.compress([input_path], output_path, compression=compression, nodes=0)

        # Check that the output file can be loaded
        with enstools.io.read(join(output_path, ds)) as ds_out:
            ds_out.load()


class TestClass:
    @classmethod
    def setup_class(cls):
        """
        This code will be executed at the beginning of the tests.
        We will be launching the
        :return:
        """
        """
        Creates two temporary directories:
        - Input directory: Will store the synthetic data created for the test
        - Output directory: Will store the compressed synthetic data
        :return: Tempdir, Tempdir
        """
        from enstools.core.tempdir import TempDir
        # Create temporary directory in which we'll put some synthetic datasets
        cls.input_tempdir = TempDir(check_free_space=False)
        cls.output_tempdir = TempDir(check_free_space=False)
        create_synthetic_dataset(cls.input_tempdir.getpath())  # noqa

    @classmethod
    def teardown_class(cls):
        # release resources
        cls.input_tempdir.cleanup()  # noqa
        cls.output_tempdir.cleanup()  # noqa

    def test_dataset_exists(self):
        input_tempdir = self.input_tempdir
        output_tempdir = self.output_tempdir
        tempdir_path = input_tempdir.getpath()

        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            assert isfile(join(tempdir_path, ds))

    def test_analyzer(self):
        from enstools.io import analyze
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            analyze(file_paths=[input_path])

    def test_zfp_analyzer(self):
        from enstools.io import analyze
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
        from enstools.io import analyze
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
        from enstools.io import analyze
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            analyze(file_paths=[input_path], compressor="sz")

    @pytest.mark.skipif(check_sz_availability(), reason="Requires SZ not being available")
    def test_sz_checker(self):
        from enstools.encoding.errors import EnstoolsCompressionError
        compression = "lossy,sz,pw_rel,0.1"
        with pytest.raises(EnstoolsCompressionError):
            wrapper(self, compression=compression)

    def test_compress_vanilla(self):
        wrapper(self)

    def test_compress_lossless(self):
        compression = "lossless"
        wrapper(self, compression=compression)

    @pytest.mark.skipif(not check_sz_availability(), reason="Requires SZ")
    def test_compress_sz_pw_rel(self):
        compression = "lossy,sz,pw_rel,0.1"
        wrapper(self, compression=compression)

    @pytest.mark.skipif(not check_sz_availability(), reason="Requires SZ")
    def test_compress_sz_abs(self):
        compression = "lossy,sz,abs,0.01"
        wrapper(self, compression=compression)

    @pytest.mark.skipif(not check_sz_availability(), reason="Requires SZ")
    def test_compress_sz_rel(self):
        compression = "lossy,sz,rel,0.001"
        wrapper(self, compression=compression)

    def test_compress_zfp_rate(self):
        compression = "lossy,zfp,rate,1"
        wrapper(self, compression=compression)

    def test_compress_zfp_accuracy(self):
        compression = "lossy,zfp,accuracy,.1"
        wrapper(self, compression=compression)

    def test_compress_zfp_precision(self):
        compression = "lossy,zfp,precision,17"
        wrapper(self, compression=compression)

    def test_compress_zfp_variable_specification(self):
        compression = "temperature:lossy,zfp,rate,1 precipitation:lossy,zfp,rate,2"
        wrapper(self, compression=compression)

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
        from enstools.io import compress
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
        from enstools.io import compress
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

    def test_zfp_filter_availability(self):
        from enstools.encoding import check_zfp_availability
        assert check_zfp_availability

    def test_specify_single_file_output_name(self):
        from enstools.io import compress
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
        from enstools.io import compress
        input_tempdir = self.input_tempdir
        output_tempdir = self.output_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            output_filename = f"{output_tempdir.getpath()}/{ds.replace('.nc', '_output.nc')}"
            # Import and launch compress function
            compress(input_path, output_filename, compression="lossless", nodes=0)

    def test_significant_bits_analysis(self):
        from enstools.io.compression.significant_bits import analyze_file_significant_bits
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(3, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            # Import and launch compress function
            analyze_file_significant_bits(input_path)

    def test_prune(self):
        from enstools.io.compression.pruner import pruner
        input_tempdir = self.input_tempdir
        output_tempdir = self.output_tempdir
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(3, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            # Import and launch compress function
            pruner(input_path, output_tempdir.getpath())

    @pytest.mark.skipif(not check_libpressio_availability(), reason="Requires libpressio")
    def test_emulation(self):
        from enstools.io import read
        from enstools.io.compression.emulation import emulate_compression_on_dataset
        input_tempdir = self.input_tempdir
        output_tempdir = self.output_tempdir
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(3, 4)]
        compression_specifications = ["lossy,sz,rel,0.1",
                                      "lossy,sz,pw_rel,0.01",
                                      "lossy,zfp,rate,1.0"
                                      ]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            # Import and launch compress function
            ds = read(input_path)
            for compression_specification in compression_specifications:
                ds, _ = emulate_compression_on_dataset(ds, compression=compression_specification)
