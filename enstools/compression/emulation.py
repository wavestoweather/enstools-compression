"""
#
# Functions to emulate the effects of compression
#

"""
from typing import Union, Tuple

import numpy
import xarray

from enstools.core import cache
from enstools.encoding.api import DatasetEncoding, NullEncoding, LosslessEncoding, LossyEncoding, Encoding
from .emulators import DefaultEmulator


def emulate_compression_on_dataset(dataset: xarray.Dataset, compression: Union[str, dict], in_place: bool = True):
    """
    Emulate the compression on an xarray dataset using the specified compression settings. This function applies
    the given compression settings to each variable in the dataset that is not a coordinate. The compression
    is either applied in-place or to a deep copy of the dataset, depending on the value of the `in_place` parameter.

    :param dataset: An xarray dataset containing the data to be compressed.
    :param compression: A string or dictionary defining the compression settings to be applied to the dataset.
                        If a string is provided, it should be a predefined compression setting.
                        If a dictionary is provided, it should have the variable names as keys and the corresponding
                        compression settings as values.
    :param in_place: A boolean value indicating whether to apply the compression in-place or to a deep copy
                     of the dataset. If True, the function returns the same dataset with compression applied.
                     If False, the function returns a compressed deep copy of the dataset.
    :return: A tuple containing the compressed dataset and a dictionary with compression metrics for each variable.
    """

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
    """
    Emulates compression on a given DataArray using the specified encoding.

    Parameters
    ----------
    data_array : xarray.DataArray
        The input data array to be compressed.
    compression_specification : Encoding
        The encoding specification to apply for the compression.
    in_place : bool, optional, default=True
        If True, modifies the input data array in place, otherwise creates a new copy.

    Returns
    -------
    data_array : xarray.DataArray
        The compressed data array.
    compression_metrics : dict
        A dictionary containing compression metrics.

    """
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
    """
        Emulates compression on a given NumPy array using the specified encoding.

    Parameters
    ----------
    data : numpy.ndarray
        The input NumPy array to be compressed.
    compression_specification : Encoding
        The encoding specification to apply for the compression.

    Returns
    -------
    decompressed : numpy.ndarray
        The decompressed NumPy array after compression.
    metrics : dict
        A dictionary containing compression metrics.

    """

    if isinstance(compression_specification, (LosslessEncoding, NullEncoding)):
        return data, {}

    emulator_backend = DefaultEmulator

    uncompressed_data = data
    decompressed_data = uncompressed_data.copy()

    compressor = emulator_backend(compression_specification, uncompressed_data=decompressed_data)

    decompressed = compressor.compress_and_decompress(decompressed_data)
    metrics = {"compression_ratio": compressor.compression_ratio()}
    return decompressed, metrics
