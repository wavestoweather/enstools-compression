"""
#
# Functions to emulate the effects of compression
#

"""
from typing import Union, Tuple
from enstools.encoding.definitions import Compressors
from enstools.encoding.api import FilterEncodingForH5py, FilterEncodingForXarray, check_libpressio_availability,\
    check_zfp_availability, check_sz_availability, check_blosc_availability
from enstools.core.errors import EnstoolsError
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
    dataset_encoding = FilterEncodingForXarray(dataset, compression)
    dataset_metrics = {}
    for variable in variables:
        var_compression = dataset_encoding.encoding()[variable]
        if var_compression and var_compression.compressor != Compressors.BLOSC:
            dataset[variable], dataset_metrics[variable] = emulate_compression_on_data_array(dataset[variable],
                                                                                             var_compression)
    if cache_was_on:                                                                                             
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
    if compression_specification.compressor in [Compressors.BLOSC, Compressors.NONE]:
        return data, {}

    # For performance reasons, Libpressio is the preferred backend for emulation.
    # It will be used if available, otherwise we will rely on the filters and
    if check_libpressio_availability():
        from enstools.compression.emulators import LibpressioEmulator
        emulator_backend = LibpressioEmulator
    else:
        from enstools.compression.emulators.FiltersEmulator import FilterEmulator
        emulator_backend = FilterEmulator
        # Check that the proper filter is actually available:
        if not check_compressor_availability(compression_specification.compressor):
            raise EnstoolsError(f"Trying to use {compression_specification.compressor!r} which is not available")

    uncompressed_data = data
    decompressed_data = uncompressed_data.copy()

    compressor = emulator_backend(
        compressor_name=compression_specification.compressor,
        mode= compression_specification.mode,
        parameter=compression_specification.parameter,
        uncompressed_data=decompressed_data)

    decompressed = compressor.compress_and_decompress(decompressed_data)
    metrics = {"compression_ratio": compressor.compression_ratio()}
    return decompressed, metrics


def check_compressor_availability(compressor: Compressors) -> bool:
    if compressor is Compressors.ZFP:
        return check_zfp_availability()
    elif compressor is Compressors.SZ:
        return check_sz_availability()
    elif compressor is Compressors.BLOSC:
        return check_blosc_availability()
    else:
        raise NotImplementedError(f"Compressor: {compressor} hasn't been implemented.")
