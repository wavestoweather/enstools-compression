from os.path import isfile, join

# List with all the available metrics
import xarray
from enstools.compression.metrics import get_matching_scores

available_metrics = get_matching_scores(arguments=["reference", "target"])

metrics = list(available_metrics.keys())

# List of metrics that require a distribution:
ensemble_metrics = [
    "continuous_ranked_probability_score",
    'kolmogorov_smirnov_multicell',
]

# Metrics that require special testing
excluded_metrics = [
    "structural_similarity_index",
    'structural_similarity_log_index',
    'ssim_I',
]


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
        input_tempdir = self.input_tempdir
        output_tempdir = self.output_tempdir
        tempdir_path = input_tempdir.getpath()

        dimensions = [1, 2, 3, 4]
        datasets = ["dataset_%iD.nc" % dimension for dimension in dimensions]
        for ds in datasets:
            assert isfile(join(tempdir_path, ds))

    def test_scalar_metrics(self):
        """
        Test non-ensemble metrics.
        """
        # Get the list of the metrics for this test
        test_metrics = [m for m in metrics if m not in ensemble_metrics and m not in excluded_metrics]
        from enstools.compression.metrics import DatasetMetrics
        from enstools.io import read
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        dimensions = [1, 2, 3, 4]
        files = ["dataset_%iD.nc" % dimension for dimension in dimensions]
        for file_name in files:
            input_path = join(input_tempdir.getpath(), file_name)
            ds = read(input_path)
            ds_metrics = DatasetMetrics(ds, ds)
            for variable in ds_metrics.variables:
                var_metrics = ds_metrics[variable]
                for metric in test_metrics:
                    m = var_metrics[metric]
                    assert isinstance(m, float) or isinstance(m, xarray.DataArray)

    def test_ensemble_metrics(self):
        """
        Test non-ensemble metrics.
        """
        # Get the list of the metrics for this test
        test_metrics = [m for m in ensemble_metrics if m not in excluded_metrics]
        from enstools.compression.metrics import DatasetMetrics
        from enstools.io import read
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        dimensions = [4]
        files = ["dataset_%iD.nc" % dimension for dimension in dimensions]
        for file_name in files:
            input_path = join(input_tempdir.getpath(), file_name)
            ds = read(input_path)
            ds_metrics = DatasetMetrics(ds, ds)
            for variable in ds_metrics.variables:
                var_metrics = ds_metrics[variable]
                for metric in test_metrics:
                    m = var_metrics[metric]
                    assert isinstance(m, float) or isinstance(m, xarray.DataArray)

    def test_ssim(self):
        """
        Test non-ensemble metrics.
        """
        # Get the list of the metrics for this test
        test_metrics = ["ssim_I"]
        from enstools.compression.metrics import DatasetMetrics
        from enstools.io import read
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        dimensions = [2, 3, 4]
        files = ["dataset_%iD.nc" % dimension for dimension in dimensions]
        for file_name in files:
            input_path = join(input_tempdir.getpath(), file_name)
            ds = read(input_path)
            ds_metrics = DatasetMetrics(ds, ds)
            for variable in ds_metrics.variables:
                var_metrics = ds_metrics[variable]
                for metric in test_metrics:
                    m = var_metrics[metric]
                    assert isinstance(m, float) or isinstance(m, xarray.DataArray)
