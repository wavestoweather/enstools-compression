import xarray
from enstools.compression.analyzer.analyzer import analyze_dataset
import enstools.compression.xr_accessor  # noqa

dataset_names = [
    "air_temperature",
    # "air_temperature_gradient",
    # "basin_mask",
    # "rasm",
    # "ROMS_example",
    # "tiny",
    # "era5-2mt-2019-03-uk.grib",
    # "eraint_uvz",
    # "ersstv5"
]


def main():
    results = {}
    failed_datasets = []
    for dataset_name in dataset_names:
        try:
            with xarray.tutorial.open_dataset(dataset_name) as dataset:
                encoding, metrics = analyze_dataset(dataset=dataset)
                results[dataset_name] = (encoding, metrics)
                dataset.to_netcdf(f"reference_{dataset_name}.nc")
                dataset.to_compressed_netcdf(f"compressed_{dataset_name}.nc", compression=encoding)
        except ValueError:
            failed_datasets.append(dataset_name)

    print(results)
    print(failed_datasets)


if __name__ == "__main__":
    main()
