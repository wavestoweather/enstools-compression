from pathlib import Path

import xarray as xr
from enstools.compression.analyzer.analyzer import analyze_dataset
import enstools.compression.xr_accessor  # noqa


dataset_names = [
    "air_temperature",
    "air_temperature_gradient",
    "basin_mask",
    "rasm",
    "ROMS_example",
    "tiny",
    "eraint_uvz",
    "ersstv5"
]


def get_compression_ratio(reference_path, compressed_path):
    reference_size = reference_path.stat().st_size
    compressed_size = compressed_path.stat().st_size

    compression_ratio = reference_size / compressed_size
    return compression_ratio


def do_analysis_on_xr_dataset(dataset_name: str) -> None:
    with xr.tutorial.open_dataset(dataset_name) as dataset:
        for var in dataset.variables:
            dataset[var].encoding = {}
        _ = analyze_dataset(dataset)


class TestDummyDatasets:
    def test_air_temperature_compression_ratio(self):
        dataset_name = "air_temperature"
        reference_path = Path(f"reference_{dataset_name}.nc")
        compressed_path = Path(f"compressed_{dataset_name}.nc")
        with xr.tutorial.open_dataset(dataset_name) as dataset:
            dataset["air"].encoding = {}
            encoding, metrics = analyze_dataset(dataset)

            dataset.to_netcdf(reference_path.as_posix())
            dataset.to_compressed_netcdf(compressed_path, compression=encoding)

            metrics_compression_ratio = metrics.get("air").get("compression_ratio")
            disk_compression_ratio = get_compression_ratio(reference_path, compressed_path)

            if reference_path.exists():
                reference_path.unlink()
            if compressed_path.exists():
                compressed_path.unlink()

            ratio = metrics_compression_ratio/disk_compression_ratio
            # Proportional tolerance
            tolerance = .2
            # We will consider that the results are good enough if the compression ratio is within a 20% error
            # of the disk compression ratio

            if not (1. - tolerance < ratio < 1+tolerance):
                raise AssertionError(metrics_compression_ratio, disk_compression_ratio)


    def test_air_temperature(self):
        do_analysis_on_xr_dataset("air_temperature")

    def test_air_temperature_gradient(self):
        do_analysis_on_xr_dataset("air_temperature_gradient")

    def test_basin_mask(self):
        do_analysis_on_xr_dataset("basin_mask")

    def test_rasm(self):
        do_analysis_on_xr_dataset("rasm")

    def test_ROMS_example(self):
        do_analysis_on_xr_dataset("ROMS_example")

    def test_tiny(self):
        do_analysis_on_xr_dataset("tiny")

    def test_eraint_uvz(self):
        do_analysis_on_xr_dataset("eraint_uvz")

    def test_ersstv5(self):
        do_analysis_on_xr_dataset("ersstv5")



