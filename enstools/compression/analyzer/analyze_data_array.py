import copy
import logging
from typing import Tuple, Type, Callable
import warnings

import numpy as np
import xarray

from enstools.core.errors import EnstoolsError
from enstools.encoding.api import compression_mode_aliases, compressor_aliases, Compressors, \
    check_libpressio_availability
from enstools.encoding.rules import COMPRESSION_SPECIFICATION_SEPARATOR
from enstools.compression.emulators.EmulatorClass import Emulator
from .AnalysisOptions import AnalysisOptions
from enstools.compression.emulators import LibpressioEmulator, ZFPEmulator, FilterEmulator
from .analyzer_utils import get_metrics, get_parameter_range, bisection_method

# These metrics will be used to select within the different encodings when aiming at a certain compression ratio.
ANALYSIS_DIAGNOSTIC_METRICS = ["correlation_I", "ssim_I"]
COMPRESSION_RATIO_LABEL = "compression_ratio"
counter = 0


def get_compressor_factory(name="libpressio") -> Type[Emulator]:
    """
    This function returns a Compressor object which is able to compress and decompress data.
    The selection here is made based on the availability of LibPressio.
    """
    if name == "filters":
        return FilterEmulator
    elif name == "zfpy":
        return ZFPEmulator
    elif name == "libpressio":
        if check_libpressio_availability():
            return LibpressioEmulator
        else:
            logging.warning("libpressio is not available, using FilterEmulator instead")
            return FilterEmulator
    else:
        raise NotImplementedError(f"Options are 'filters', 'zfpy' and 'libpressio'")



def analyze_data_array(data_array: xarray.DataArray, options: AnalysisOptions) -> Tuple[str, dict]:
    """
    Find the compression specification corresponding to a certain data array and a given set of compression options.
    """
    # In case there is a time dimension, select the last element.
    # There are accumulative variables (like total precipitation) which have mostly 0 on the first time step.
    # Using the last time-step can represent an advantage somehow.
    if "time" in data_array.dims:
        data_array = data_array.isel(time=-1)
    # Check if the array contains any nan
    contains_nan = np.isnan(data_array.values).any()
    if contains_nan:
        logging.warning(f"The variable {data_array.name!r} contains NaN. Falling to 'lossless'.\n"
                        "It is possible to prevent that replacing the NaN values using the parameter --fill-na")
        return "lossless", {**{COMPRESSION_RATIO_LABEL: 1.0}, **{met: 0. for met in ANALYSIS_DIAGNOSTIC_METRICS}}

    # Define the functions that will be used to find optimal parameters
    get_metric_from_parameter, function_to_nullify, constrain = define_functions_to_optimize(data_array, options)

    # Define parameter range
    parameter_range = get_parameter_range(data_array, options)

    # If the aim is a specific compression ratio, the parameter range needs to be reversed
    # because the relation between compression ratio and quality is inverse.
    if COMPRESSION_RATIO_LABEL in options.thresholds:
        parameter_range = tuple(reversed(parameter_range))

    #  Ignore warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        direct_relation = not (COMPRESSION_RATIO_LABEL in options.thresholds)
        direct_relation = True
        # Use bisection method to find optimal compression parameter.
        parameter = bisection_method(
            parameter_range,
            constrain=constrain,
            fun=function_to_nullify,
            direct_relation=direct_relation)

        # Compute metrics
        # When aiming for a compression ratio some other metrics need to be provided too.
        if COMPRESSION_RATIO_LABEL not in options.thresholds:
            metrics = get_metric_from_parameter(parameter)
        else:
            new_options = copy.copy(options)
            for m in ANALYSIS_DIAGNOSTIC_METRICS:
                new_options.thresholds[m] = 1
            get_metric_from_parameter, _, _ = define_functions_to_optimize(data_array, new_options)
            metrics = get_metric_from_parameter(parameter)

    # Define compression specification
    separator = COMPRESSION_SPECIFICATION_SEPARATOR
    compression_spec = f"{separator}".join(["lossy",
                                            compressor_aliases[options.compressor],
                                            compression_mode_aliases[options.mode],
                                            f"{parameter:.3g}",
                                            ])

    logging.debug(f"Evaluated the function {counter} times.")
    return compression_spec, metrics


def define_functions_to_optimize(data_array: xarray.DataArray, options: AnalysisOptions) -> \
        Tuple[Callable, Callable, Callable]:
    """
    Function to get methods that will be used to perform a bisection method and find proper compression parameters.
    """
    thresholds = options.thresholds
    global counter
    counter = 0

    compressor_factory = get_compressor_factory()

    # Using a cache allows us to avoid recomputing when using the same parameters.
    # @functools.lru_cache
    def get_metrics_from_parameter(parameter: float) -> dict:
        """
        This function will return a dictionary with different metrics computed with data that has been compressed
        with a specific parameter.
        """
        global counter
        counter += 1

        if compressor_factory == ZFPEmulator and options.compressor != Compressors.ZFP:
            raise EnstoolsError(f"Trying to use ZFP analysis compressor for compressor {options.compressor}")

        target = data_array.copy(deep=True)

        # Set buffers
        uncompressed_data = data_array.values
        # Create compressor for case
        analysis_compressor = compressor_factory(options.compressor, options.mode, parameter, uncompressed_data)
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
        return min([metrics[metric] - options.thresholds[metric] for metric in thresholds.keys()])

    def constrain(parameter):
        """
        If the value of the function_to_nullify is positive it means that the thresholds are fulfilled.
        """
        return function_to_nullify(parameter) >= 0.

    return get_metrics_from_parameter, function_to_nullify, constrain
