import logging
from typing import List, Dict, Callable

import numpy as np
import xarray

from enstools.core.errors import EnstoolsError
from enstools.compression.analyzer.AnalysisOptions import AnalysisOptions
from enstools.compression.metrics import DataArrayMetrics
from enstools.encoding.definitions import lossy_compressors_and_modes


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
    It means that for absolute and relative threshold modes the bigger value goes first.
    :param data_array:
    :param options:
    :return:
    """

    # TODO: Would be better to centralize the valid numbers for parameters in a single place.

    # For absolute threshold mode,
    if options.mode in ["abs", "accuracy"]:
        value_range = float(data_array.max() - data_array.min())
        looser, tighter = value_range, 0.

    # For relative threshold modes
    elif options.mode in ["rel", "pw_rel"]:
        looser, tighter = 1., 0.

    # For zfp rate
    elif options.mode in ["rate"]:
        looser, tighter = 1., 32.

    # For zfp precision
    elif options.mode == "precision":
        looser, tighter = 2, 32

    elif options.mode in ["norm2", "psnr"]:
        looser, tighter = lossy_compressors_and_modes["sz3"][options.mode]
        return looser, tighter

    # If the mode is not known raise an exception
    else:
        raise EnstoolsError(f"Mode {options.mode} not implemented.")

    return looser, tighter


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
    looser, tighter = parameter_range

    if isinstance(looser, float):
        return continuous_bisection_method(parameter_range, fun, constrain, depth, max_depth, last_value,
                                           retry_repeated, threshold, direct_relation)
    elif isinstance(looser, int):
        parameter_values = list(range(looser, tighter + 1))
        return discrete_bisection_method(parameter_values, fun, constrain, depth, max_depth, last_value,
                                         retry_repeated, threshold, direct_relation)
    else:
        raise TypeError(f"Expecting float or int. Got {type(looser)}")


def continuous_bisection_method(parameter_range: tuple,
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

    return continuous_bisection_method((new_start, new_end),
                                       fun=fun,
                                       constrain=constrain,
                                       depth=depth + 1,
                                       last_value=value_at_middle,
                                       retry_repeated=retry_repeated,
                                       threshold=threshold,
                                       direct_relation=direct_relation,
                                       )


def discrete_bisection_method(parameters_list: list,
                              fun: callable = None,
                              constrain: callable = None,
                              depth: int = 0,
                              max_depth: int = 50,
                              last_value=None,
                              retry_repeated=5,
                              threshold=0.1,
                              direct_relation=True,
                              ):
    length = len(parameters_list)
    middle_index = length // 2
    middle = parameters_list[middle_index]

    def comparison(value_at_middle: float, direct_relation: bool = True):
        return (value_at_middle > 0.0) == direct_relation

    # Evaluate at the middle point
    value_at_middle = fun(middle)
    logging.debug(f"{middle}{float(value_at_middle)=}")

    # If the value at the middle is positive (all thresholds are fulfilled) we can return the parameter at the middle,
    # otherwise select the safer one.
    parameter_to_return = middle if value_at_middle > 0.0 else parameters_list[-1]

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
        new_parameters_list = parameters_list[:middle_index]

    else:
        new_parameters_list = parameters_list[middle_index:]

    return discrete_bisection_method(new_parameters_list,
                                     fun=fun,
                                     constrain=constrain,
                                     depth=depth + 1,
                                     last_value=value_at_middle,
                                     retry_repeated=retry_repeated,
                                     threshold=threshold,
                                     direct_relation=direct_relation,
                                     )
