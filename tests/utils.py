def create_synthetic_dataset(directory: str) -> None:
    """
    Creates three synthetic netcdf datasets (1d,2d,3d) into the provided directory.
    :param directory:
    :return: None
    """
    import numpy as np
    import xarray as xr
    import pandas as pd
    from scipy.ndimage import gaussian_filter
    from os.path import join
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


def file_size(file_path) -> int:
    from pathlib import Path
    return Path(file_path).stat().st_size


def wrapper(cls, compression=None):
    import enstools.compression.api
    import enstools.io
    from os.path import join
    input_tempdir = cls.input_tempdir
    output_tempdir = cls.output_tempdir
    # Check that the compression without specifying compression parameters works
    datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
    for ds in datasets:
        input_path = join(input_tempdir.getpath(), ds)
        output_path = output_tempdir.getpath()
        # Import and launch compress function
        enstools.compression.api.compress([input_path], output_path, compression=compression, nodes=0)

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