"""
#
# Functions to emulate the effects of compression
#

"""
from typing import Union, Tuple
from enstools.encoding.definitions import Compressors
from enstools.encoding.encodings import FilterEncodingForH5py, FilterEncodingForXarray
import xarray
import numpy

from enstools.core.errors import EnstoolsError


def emulate_compression_on_dataset(dataset: xarray.Dataset, compression: Union[str, dict], in_place: bool = True):
    """

    :param dataset:
    :param compression:
    :param in_place: if True, it returns the same dataset, if False it makes a copy.
    :return:
    """
    from enstools.core import cache
    cache.unregister()
    if not in_place:
        dataset = dataset.copy(deep=True)
    # List variables that aren't coordinates
    variables = [v for v in dataset.variables if v not in dataset.coords]

    #
    dataset_encoding = FilterEncodingForXarray(dataset, compression)
    dataset_metrics = {}
    for variable in variables:
        var_compression = dataset_encoding.encoding()[variable]
        if var_compression and var_compression.compressor != Compressors.BLOSC:
            dataset[variable], dataset_metrics[variable] = emulate_compression_on_data_array(dataset[variable],
                                                                                             var_compression)
    cache.register()
    return dataset, dataset_metrics


def emulate_compression_on_data_array(data_array: xarray.DataArray, compression_specification: FilterEncodingForH5py,
                                      in_place=True) -> Tuple[xarray.DataArray, dict]:
    if not in_place:
        data_array = data_array.copy()
    # For now we want to apply compression chunk by chunk ( or at least for the moment avoid using multiple time-steps)
    if "time" not in data_array.coords:
        data_array.values, compression_metrics = emulate_compression_on_numpy_array(data_array.values,
                                                                                    compression_specification)
    else:
        for time in data_array["time"]:
            data_array.loc[{"time": time}], compression_metrics = emulate_compression_on_numpy_array(
                data_array.sel(time=time).values, compression_specification)
    return data_array, compression_metrics


def emulate_compression_on_numpy_array(data: numpy.ndarray, compression_specification: FilterEncodingForH5py) -> \
        Tuple[numpy.ndarray, dict]:
    # TODO: Ugly dependency, maybe think about a better place to put that.

    if compression_specification.compressor in [Compressors.BLOSC, Compressors.NONE]:
        return data, {}
    from enstools.compression.analyzer.LibpressioAnalysisCompressor import compressor_configuration
    try:
        from libpressio import PressioCompressor
    except ModuleNotFoundError as err:
        raise EnstoolsError(
            "The library libpressio its not available, can not proceed with emulation.")
    uncompressed_data = data
    decompressed_data = uncompressed_data.copy()

    compressor_name = compression_specification.compressor
    mode = compression_specification.mode
    parameter = compression_specification.parameter
    # compressor_name, mode, parameter = parse_compression(compression_specification)
    config = compressor_configuration(compressor_name, mode, parameter, data)
    compressor = PressioCompressor.from_config(config)

    # preform compression and decompression
    compressed = compressor.encode(uncompressed_data)
    decompressed = compressor.decode(compressed, decompressed_data)
    metrics = compressor.get_metrics()
    return decompressed, metrics
