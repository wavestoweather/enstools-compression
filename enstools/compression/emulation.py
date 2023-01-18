"""
#
# Functions to emulate the effects of compression
#

"""
from typing import Union, Tuple
from enstools.encoding.api import DatasetEncoding, NullEncoding, LosslessEncoding, LossyEncoding, Encoding
from .emulators import default_emulator
import xarray
import numpy


def emulate_compression_on_dataset(dataset: xarray.Dataset, compression: Union[str, dict], in_place: bool = True):
    """

    :param dataset:
    :param compression:
    :param in_place: if True, it returns the same dataset, if False it makes a copy.
    :return:
    """
    from enstools.core import cache
    try:
        cache.unregister()
        cache_was_on = True
    except KeyError:
        cache_was_on = False
    if not in_place:
        dataset = dataset.copy(deep=True)
    # List variables that aren't coordinates
    variables = [v for v in dataset.variables if v not in dataset.coords]

    #
    dataset_encoding = DatasetEncoding(dataset, compression)
    dataset_metrics = {}
    for variable in variables:
        var_compression = dataset_encoding.encoding()[variable]
        if var_compression and isinstance(var_compression, LossyEncoding):
            dataset[variable], dataset_metrics[variable] = emulate_compression_on_data_array(dataset[variable],
                                                                                             var_compression)
    if cache_was_on:
        cache.register()
    return dataset, dataset_metrics


def emulate_compression_on_data_array(data_array: xarray.DataArray, compression_specification: Encoding,
                                      in_place=True) -> Tuple[xarray.DataArray, dict]:
    if not in_place:
        data_array = data_array.copy()
    # For now we want to apply compression chunk by chunk ( or at least for the moment avoid using multiple time-steps)
    # if "time" not in data_array.dims:
    #     data_array.values, compression_metrics = emulate_compression_on_numpy_array(data_array.values,
    #                                                                                 compression_specification)
    # else:
    #     for time in data_array["time"]:
    #         data_array.loc[{"time": time}], compression_metrics = emulate_compression_on_numpy_array(
    #             data_array.sel(time=time).values, compression_specification)

    # FIXME: I don't separate the time-steps at that point anymore because of performance penalty.
    data_array.values, compression_metrics = emulate_compression_on_numpy_array(data_array.values,
                                                                                compression_specification)

    return data_array, compression_metrics


def emulate_compression_on_numpy_array(data: numpy.ndarray, compression_specification: Encoding) -> \
        Tuple[numpy.ndarray, dict]:
    if isinstance(compression_specification, LosslessEncoding) or \
            isinstance(compression_specification, NullEncoding):
        return data, {}

    emulator_backend = default_emulator

    uncompressed_data = data
    decompressed_data = uncompressed_data.copy()

    compressor = emulator_backend(compression_specification, uncompressed_data=decompressed_data)

    decompressed = compressor.compress_and_decompress(decompressed_data)
    metrics = {"compression_ratio": compressor.compression_ratio()}
    return decompressed, metrics
