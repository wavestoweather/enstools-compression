import logging
from typing import List, Dict, Callable

import numpy as np
import xarray

from enstools.core.errors import EnstoolsError
from enstools.compression.analyzer.AnalysisOptions import AnalysisOptions
from enstools.encoding.api import Compressors, CompressionModes
from enstools.compression.metrics import DataArrayMetrics


def get_metrics(reference_data: xarray.DataArray, recovered_data: xarray.DataArray, metric_names: List[str],
                **kwargs) -> Dict[str, float]:
    metrics = DataArrayMetrics(reference_data, recovered_data)
    return {metric: float(metrics[metric]) for metric in metric_names if metric != "compression_ratio"}


def check_compression_ratio(compression_ratio: float, thresholds: dict, **kwargs):
    return compression_ratio > thresholds["compression_ratio"]


def get_parameter_range(data_array: xarray.DataArray, options: AnalysisOptions):
    """
    Define the parameter range given a data-array and a set of compression options.
    It returns a tuple with the lower and the higher bound of the parameter range.
    The lower bound represents the looser parameter and the higher bound represents the tighter parameter.
    :param data_array:
    :param options:
    :return:
    """

    if options.compressor is Compressors.ZFP:
        if options.mode == CompressionModes.RATE:
            # A minimum rate of 0.1 leads to failure during compression.
            MIN_RATE = 1.
            MAX_RATE = 32.
            return MIN_RATE, MAX_RATE
        elif options.mode == CompressionModes.PRECISION:
            MIN_PRECISION = 2.
            MAX_PRECISION = 32.
            return MIN_PRECISION, MAX_PRECISION
        elif options.mode == CompressionModes.ACCURACY:
            value_range = float(data_array.max() - data_array.min())
            # return 0., value_range
            return value_range, 0.
        else:
            raise EnstoolsError(f"Problem in {__file__}")
    elif options.compressor is Compressors.SZ:
        if options.mode == CompressionModes.ABS:
            value_range = float(data_array.max() - data_array.min())
            return value_range, 0.
        elif options.mode in [CompressionModes.REL, CompressionModes.PW_REL]:
            MIN_REL = 0.
            MAX_REL = 1.
            return MAX_REL, MIN_REL
        else:
            raise EnstoolsError(f"Problem in {__file__}")
    else:
        raise EnstoolsError(f"Problem in {__file__}")


def bisection_method(parameter_range: tuple,
                     fun: callable = None,
                     constrain: callable = None,
                     depth: int = 0,
                     max_depth: int = 50,
                     last_value=None,
                     retry_repeated=5,
                     threshold=0.1,
                     direct_relation=True,
                     ):
    # Get start and end from parameter range
    start, end = parameter_range

    # Get the middle point
    middle = (start + end) / 2

    def comparison(value_at_middle: float, direct_relation: bool = True):
        return (value_at_middle > 0.0) == direct_relation

    # Evaluate at the middle point
    value_at_middle = fun(middle)
    # TODO: use logging and a debug mode to print this kind of things
    logging.debug(f"{start=:.2e},{end=:.2e}{float(value_at_middle)=}")

    # If the value at the middle is positive (all thresholds are fulfilled) we can return the parameter at the middle,
    # otherwise select the safer one.
    parameter_to_return = middle if value_at_middle > 0.0 else end

    # In case the accuracy exit condition is reached, return the parameter value at that point
    if 0.0 <= value_at_middle < threshold:
        return parameter_to_return

    # If the value is the same that the last try, we can retry few times
    if value_at_middle == last_value:
        if retry_repeated == 0:
            return parameter_to_return
        else:
            retry_repeated -= 1

    # In case having reached the maximum depth, return the proper value
    if depth >= max_depth:
        return parameter_to_return

    # # Otherwise, set new parameter range and call the function again
    if comparison(value_at_middle, direct_relation=direct_relation):
        new_start, new_end = start, middle
    else:
        new_start, new_end = middle, end

    return bisection_method((new_start, new_end),
                            fun=fun,
                            constrain=constrain,
                            depth=depth + 1,
                            last_value=value_at_middle,
                            retry_repeated=retry_repeated,
                            threshold=threshold,
                            direct_relation=direct_relation,
                            )
