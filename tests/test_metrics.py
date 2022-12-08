from os.path import isfile, join

# List with all the available metrics
from pathlib import Path
from typing import List

import xarray
from enstools.compression.metrics import get_matching_scores
from utils import TestClass

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


def wrapper_to_test_metrics(input_folder: Path, dimensions: List[int], test_metrics: List[str]):
    from enstools.compression.metrics import DatasetMetrics
    from enstools.io import read
    file_names = ("dataset_%iD.nc" % dimension for dimension in dimensions)
    file_paths = (input_folder / file_name for file_name in file_names)

    for file_path in file_paths:
        with read(file_path) as ds:
            ds_metrics = DatasetMetrics(ds, ds)
            for variable in ds_metrics.variables:
                var_metrics = ds_metrics[variable]
                for metric in test_metrics:
                    m = var_metrics[metric]
                    assert isinstance(m, float) or isinstance(m, xarray.DataArray)


class TestMetrics(TestClass):
    def test_dataset_exists(self):
        dimensions = [1, 2, 3, 4]
        file_names = ("dataset_%iD.nc" % dimension for dimension in dimensions)
        file_paths = (self.input_directory_path / file_name for file_name in file_names)
        for file_path in file_paths:
            assert file_path.is_file()

    def test_scalar_metrics(self):
        """
        Test non-ensemble metrics.
        """
        # Get the list of the metrics for this test
        test_metrics = [m for m in metrics if m not in ensemble_metrics and m not in excluded_metrics]
        dimensions = [1, 2, 3, 4]
        wrapper_to_test_metrics(
            input_folder=self.input_directory_path,
            dimensions=dimensions,
            test_metrics=test_metrics,
        )

    def test_ensemble_metrics(self):
        """
        Test non-ensemble metrics.
        """
        # Get the list of the metrics for this test
        test_metrics = [m for m in ensemble_metrics if m not in excluded_metrics]
        # For ensemble metrics we need variables with an ensemble dimension, in this case only the 4D file.
        dimensions = [4]
        wrapper_to_test_metrics(
            input_folder=self.input_directory_path,
            dimensions=dimensions,
            test_metrics=test_metrics,
        )

    def test_ssim(self):
        """
        Test non-ensemble metrics.
        """
        # Get the list of the metrics for this test
        test_metrics = ["ssim_I"]
        # We can't use SSIM on 1D data
        dimensions = [2, 3, 4]
        wrapper_to_test_metrics(
            input_folder=self.input_directory_path,
            dimensions=dimensions,
            test_metrics=test_metrics,
        )

    def test_convert_size(self):
        from enstools.compression.size_metrics import readable_size
        file_path = self.input_directory_path / "dataset_2D.nc"
        readable_size(file_path)
