"""
This module provides functions to find the compression specification that corresponds
to a given data array and a set of compression options.

The main function, `analyze_data_array`, takes a `data_array` and an `options` object
and returns the compression specification and metrics computed with the compressed data.

The functions use a bisection method to find the optimal compression parameter that meets
quality requirements.
"""
# pylint: disable=W0603
import copy
import logging
import warnings
from typing import Tuple, Callable

import numpy as np
import xarray

import enstools.encoding.chunk_size
from enstools.compression.emulators import DefaultEmulator
from enstools.compression.errors import ConditionsNotFulfilledError
from enstools.compression.slicing import MultiDimensionalSliceCollection
from enstools.encoding.api import VariableEncoding
from enstools.encoding.dataset_encoding import find_chunk_sizes, convert_to_bytes
from enstools.encoding.rules import COMPRESSION_SPECIFICATION_SEPARATOR
from .analysis_options import AnalysisOptions
from .analyzer_utils import get_metrics, get_parameter_range, bisection_method

# These metrics will be used to select within the different encodings when aiming at a certain compression ratio.
ANALYSIS_DIAGNOSTIC_METRICS = ["correlation_I", "ssim_I"]
COMPRESSION_RATIO_LABEL = "compression_ratio"

COUNTER = 0


def find_direct_relation(parameter_range, function_to_nullify):
    """Return whether the nullified function has a direct relation between the parameter and the nullified value."""
    min_val, max_val = parameter_range
    first_percentile = min_val + (max_val - min_val) / 100
    last_percentile = min_val + 99 * (max_val - min_val) / 100

    eval_first_percentile = function_to_nullify(first_percentile)
    eval_last_percentile = function_to_nullify(last_percentile)
    return eval_last_percentile > eval_first_percentile


def  get_one_slice(data_array: xarray.DataArray, chunk_size: str = "100KB"):
    chunk_memory_size = convert_to_bytes(chunk_size)
    chunk_sizes = find_chunk_sizes(data_array, chunk_memory_size)
    chunk_sizes = [chunk_sizes[dim] for dim in data_array.dims]
    multi_dimensional_slice = MultiDimensionalSliceCollection(shape=data_array.shape, chunk_sizes=chunk_sizes)
    big_chunk_size = max(set([s.size for s in multi_dimensional_slice.objects.ravel()]))
    big_chunks = [s for s in multi_dimensional_slice.objects.ravel() if s.size == big_chunk_size]

    return {dim: size for dim, size in zip(data_array.dims, big_chunks[0].slices)}



def analyze_data_array(data_array: xarray.DataArray, options: AnalysisOptions) -> Tuple[str, dict]:
    """
    Find the compression specification corresponding to a certain data array and a given set of compression options.
    """

    slices = get_one_slice(data_array,
                           chunk_size=enstools.encoding.chunk_size.analysis_chunk_size)
    data_array = data_array.isel(**slices)
    # Check if the array contains any nan
    contains_nan = np.isnan(data_array.values).any()
    if contains_nan:
        logging.warning("The variable %scontains NaN. Falling to 'lossless'.\n"
                        "It is possible to prevent that replacing the NaN values using the parameter --fill-na",
                        data_array.name)
        return "lossless", {**{COMPRESSION_RATIO_LABEL: 1.0}, **{met: 0. for met in ANALYSIS_DIAGNOSTIC_METRICS}}

    # Define the functions that will be used to find optimal parameters
    get_metric_from_parameter, function_to_nullify, constrain = define_functions_to_optimize(data_array, options)

    # Define parameter range
    parameter_range = get_parameter_range(data_array, options)

    #  Ignore warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        direct_relation = find_direct_relation(parameter_range=parameter_range, function_to_nullify=function_to_nullify)
        # Use bisection method to find optimal compression parameter.
        parameter = bisection_method(
            parameter_range,
            constrain=constrain,
            fun=function_to_nullify,
            direct_relation=direct_relation)

        if not constrain(parameter):
            raise ConditionsNotFulfilledError("Condition not fulfilled!")
        # Compute metrics
        # When aiming for a compression ratio some other metrics need to be provided too.
        if COMPRESSION_RATIO_LABEL not in options.thresholds:
            metrics = get_metric_from_parameter(parameter)
        else:
            new_options = copy.deepcopy(options)
            for metric in ANALYSIS_DIAGNOSTIC_METRICS:
                new_options.thresholds[metric] = 1
            get_metric_from_parameter, _, _ = define_functions_to_optimize(data_array, new_options)
            metrics = get_metric_from_parameter(parameter)

    # Define compression specification
    separator = COMPRESSION_SPECIFICATION_SEPARATOR
    compression_spec = f"{separator}".join(["lossy",
                                            options.compressor,
                                            options.mode,
                                            f"{parameter:.3g}",
                                            ])

    logging.debug("Evaluated the function %d times.", COUNTER)
    return compression_spec, metrics


def define_functions_to_optimize(data_array: xarray.DataArray, options: AnalysisOptions) -> \
        Tuple[Callable, Callable, Callable]:
    """
    Function to get methods that will be used to perform a bisection method and find proper compression parameters.
    """
    thresholds = options.thresholds
    global COUNTER
    COUNTER = 0

    # Using a cache allows us to avoid recomputing when using the same parameters.
    # @functools.lru_cache
    def get_metrics_from_parameter(parameter: float) -> dict:
        """
        This function will return a dictionary with different metrics computed with data that has been compressed
        with a specific parameter.
        """
        global COUNTER
        COUNTER += 1

        target = data_array.copy(deep=True)

        # Set buffers
        uncompressed_data = data_array.values

        # Get encoding from options:
        encoding = VariableEncoding(compressor=options.compressor, mode=options.mode, parameter=parameter)
        # Create compressor for case
        analysis_compressor = DefaultEmulator(encoding, uncompressed_data)
        # Compress and decompress data
        decompressed = analysis_compressor.compress_and_decompress(uncompressed_data)
        # Assign values to target data_array (need to use enstools metrics)
        target.values = decompressed

        # Get compression ratio
        compression_ratio = analysis_compressor.compression_ratio()
        metrics = get_metrics(data_array, target, [*thresholds])
        metrics["compression_ratio"] = compression_ratio
        return metrics

    def function_to_nullify(parameter):
        """
        Our parameter will be optimal when the value of this function is 0.
        Which would be the less strict value that fulfills the quality requirements.

        """
        metrics = get_metrics_from_parameter(parameter)
        return min(metrics[metric] - options.thresholds[metric] for metric in thresholds.keys())

    def constrain(parameter):
        """
        If the value of the function_to_nullify is positive it means that the thresholds are fulfilled.
        """
        return function_to_nullify(parameter) >= 0.

    return get_metrics_from_parameter, function_to_nullify, constrain
