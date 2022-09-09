"""
Tests for the commandline interface.
"""

from os.path import isfile, join

import pytest


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
    nx, ny, nz, m, t = 30, 30, 5, 5, 5
    lon = np.linspace(-180, 180, nx)
    lat = np.linspace(-90, 90, ny)
    levels = np.array(range(nz))
    for dimension in [1, 2, 3, 4]:
        if dimension == 1:
            data_size = (t, nx)
            var_dimensions = ["time", "lon"]
        elif dimension == 2:
            data_size = (t, nx, ny)
            var_dimensions = ["time", "lon", "lat"]
        elif dimension == 3:
            data_size = (t, nz, nx, ny)
            var_dimensions = ["time", "level", "lon", "lat"]
        elif dimension == 4:
            data_size = (t, m, nz, nx, ny)
            var_dimensions = ["time", "ens", "level", "lon", "lat"]
        else:
            raise NotImplementedError()

        temp = 15 + 8 * np.random.randn(*data_size)
        temp = gaussian_filter(temp, sigma=5)
        precip = 10 * np.random.rand(*data_size)
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
        create_synthetic_dataset(cls.input_tempdir.getpath())

    @classmethod
    def teardown_class(cls):
        # release resources
        cls.input_tempdir.cleanup()
        cls.output_tempdir.cleanup()

    def test_dataset_exists(self):
        """
        Check that the data sets used for the test exist
        """
        input_tempdir = self.input_tempdir
        tempdir_path = input_tempdir.getpath()

        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            assert isfile(join(tempdir_path, ds))

    def test_help(self, mocker):
        """
        Check that the cli prints the help and exists.
        """
        import enstools.compression
        commands = ["_", "-h"]
        mocker.patch("sys.argv", commands)
        with pytest.raises(SystemExit):
            enstools.compression.cli()

    def test_compress(self, mocker):
        """
        Test enstools-compressor compress
        """
        import enstools.compression
        input_tempdir = self.input_tempdir
        tempdir_path = input_tempdir.getpath()
        output_tempdir = self.output_tempdir
        output_path = output_tempdir.getpath()

        file_name = "dataset_%iD.nc" % 3
        file_path = join(tempdir_path, file_name)
        output_file_path = join(output_path, file_name)
        commands = ["_", "compress", file_path, "-o", output_file_path]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli()
        assert isfile(output_file_path)

    def test_compress_with_compression_specification(self, mocker):
        """
        Test enstools-compressor compress
        """
        import enstools.compression
        input_tempdir = self.input_tempdir
        tempdir_path = input_tempdir.getpath()
        output_tempdir = self.output_tempdir
        output_path = output_tempdir.getpath()

        file_name = "dataset_%iD.nc" % 3
        file_path = join(tempdir_path, file_name)
        output_file_path = join(output_path, file_name)
        compression = "temperature:lossy,zfp,rate,3.2 precipitation:lossy,zfp,rate,1.6 default:lossless"
        commands = ["_", "compress", file_path, "-o", output_file_path, "--compression", compression]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli()
        assert isfile(output_file_path)

    def test_analyze(self, mocker):
        """
        Test enstools-compressor analyze
        """
        import enstools.compression
        input_tempdir = self.input_tempdir
        tempdir_path = input_tempdir.getpath()

        file_name = "dataset_%iD.nc" % 3
        file_path = join(tempdir_path, file_name)
        commands = ["_", "analyze", file_path]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli()

    def test_inverse_analyze(self, mocker):
        """
        Test enstools-compressor analyze in compression ratio mode.
        """
        import enstools.compression
        input_tempdir = self.input_tempdir
        tempdir_path = input_tempdir.getpath()

        file_name = "dataset_%iD.nc" % 3
        file_path = join(tempdir_path, file_name)
        commands = ["_", "analyze", file_path, "--compression-ratio", "5"]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli()

    def test_evaluator(self, mocker):
        """
        Test enstools-compressor evaluate
        """
        import enstools.compression
        input_tempdir = self.input_tempdir
        tempdir_path = input_tempdir.getpath()

        file_name = "dataset_%iD.nc" % 3
        file_path = join(tempdir_path, file_name)
        commands = ["_", "evaluate", "-r", file_path, "-t", file_path]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli()

    def test_significand(self, mocker):
        """
        Test enstools-compressor significand
        """
        import enstools.compression
        input_tempdir = self.input_tempdir
        tempdir_path = input_tempdir.getpath()

        file_name = "dataset_%iD.nc" % 3
        file_path = join(tempdir_path, file_name)
        commands = ["_", "significand", file_path]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli()

    def test_pruner(self, mocker):
        """
        Test enstools-compressor prune
        """
        import enstools.compression
        input_tempdir = self.input_tempdir
        tempdir_path = input_tempdir.getpath()

        output_tempdir = self.output_tempdir
        output_path = output_tempdir.getpath()

        file_name = "dataset_%iD.nc" % 3
        file_path = join(tempdir_path, file_name)
        commands = ["_", "prune", file_path, "-o", output_path]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli()
