"""
This module contains some helper functions that are used in analyzer.
"""

import logging
from typing import List, Dict

import xarray

from enstools.compression.analyzer.analysis_options import AnalysisOptions
from enstools.compression.metrics import DataArrayMetrics
from enstools.core.errors import EnstoolsError
from enstools.encoding.definitions import lossy_compressors_and_modes


def get_metrics(reference_data: xarray.DataArray, recovered_data: xarray.DataArray, metric_names: List[str]) \
        -> Dict[str, float]:
    """
    Calculates the requested metrics for a given pair of reference and recovered data arrays.
    :param reference_data: the reference data array
    :param recovered_data: the recovered data array
    :param metric_names: a list of metric names to calculate
    :return: a dictionary with the requested metrics
    """
    metrics = DataArrayMetrics(reference_data, recovered_data)
    return {metric: float(metrics[metric]) for metric in metric_names if metric != "compression_ratio"}


def check_compression_ratio(compression_ratio: float, thresholds: dict):
    """
    Checks whether the given compression ratio is above the given threshold.
    :param compression_ratio: the compression ratio to check
    :param thresholds: a dictionary containing the threshold values
    :return: True if the compression ratio is above the threshold, False otherwise
    """
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
    """
    Perform the bisection method to find the threshold parameter that satisfies the constraint function

    Parameters
    ----------
    parameter_range : tuple
        The range of values to search for the parameter.
    fun : callable
        The function to optimize. It must take a parameter as input and return a float as output.
    constrain : callable
        A function that returns a boolean indicating if the current value of the function `fun` satisfies some
        constraint. If None is given, no constraint is applied.
    depth : int
        The depth of the recursion. It is used to stop the recursion if it becomes too deep.
    max_depth : int
        The maximum depth of recursion.
    last_value : float, optional
        The last value obtained from `fun`.
    retry_repeated : int, optional
        The number of times to retry the method if the value obtained from `fun` is repeated.
    threshold : float, optional
        The threshold for stopping the recursion. If the absolute value of the difference between the last value
        and the current value is smaller than `threshold`, the method returns the current value.
    direct_relation : bool, optional
        If True, it is assumed that a direct relation between the parameter and the function exists. Otherwise, it is
        assumed that an inverse relation exists.

    Returns
    -------
    float
        The optimal value of the parameter.

    Raises
    ------
    TypeError
        If the type of the parameter is not float or int.

    """
    looser, tighter = parameter_range

    if isinstance(looser, float):
        return continuous_bisection_method(parameter_range, fun, constrain, depth, max_depth, last_value,
                                           retry_repeated, threshold, direct_relation)

    if isinstance(looser, int):
        parameter_values = list(range(looser, tighter + 1))
        return discrete_bisection_method(parameter_values, fun, constrain, depth, max_depth, last_value,
                                         retry_repeated, threshold, direct_relation)

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
    """
    Recursively refine a parameter range by evaluating the parameter that lies in the middle of the range.
    If the evaluation of the middle parameter returns a value greater than zero,
    the looser half of the parameter range is rejected.
    Otherwise, the tighter half of the parameter range is rejected.
    This way the bisection is iterated until the exit conditions are met.

    :param parameter_range: A tuple with the lower and upper bounds of the parameter.
    :param fun: A callable that takes the parameter as the only argument and returns the value of a function.
    :param constrain: A callable that can be used to impose additional constraints on the parameter
                      (not yet implemented).
    :param depth: The current depth of the recursion.
    :param max_depth: The maximum allowed depth of the recursion.
    :param last_value: The result of the previous call to fun.
    :param retry_repeated: The number of times the function will retry if the result is repeated (e.g., is 0.0 twice).
    :param threshold: The threshold that will stop the bisection if a value less than the threshold is obtained.
    :param direct_relation: If True, the relation between the function and the parameter is direct, that is,
                            increasing the parameter will increase the function value. If False, the relation is
                            inverse, that is, increasing the parameter will decrease the function value.
    :return: The best value of the parameter that meets the exit conditions.
    """
    # Get start and end from parameter range
    start, end = parameter_range

    # Get the middle point
    middle = (start + end) / 2

    def comparison(value_at_middle: float, direct_relation: bool = True):
        return (value_at_middle > 0.0) == direct_relation

    # Evaluate at the middle point
    value_at_middle = fun(middle)
    # TODO: use logging and a debug mode to print this kind of things
    logging.debug("start=%.2e,end=%.2e value_at_middle=%f", start, end, float(value_at_middle))

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
    """
    Apply the bisection method on a set of discrete parameters.

    :param parameters_list: List of discrete parameters.
    :param fun: Callable function to apply the method.
    :param constrain: Callable function that will return a boolean indicating if a parameter is within the defined
    range. The parameter has to be specified as a keyword argument.
    :param depth: Current depth of the recursive call.
    :param max_depth: Maximum depth of the recursive call.
    :param last_value: The last value tried by the method.
    :param retry_repeated: Number of times to retry when the value is repeated.
    :param threshold: The threshold for the method exit condition.
    :param direct_relation: Boolean indicating whether the relation between the parameter and the function value is
    direct or inverse.

    :return: The parameter value that satisfies the constrain function.

    :raises: Exception if the maximum depth is reached.
    """
    middle_index = len(parameters_list) // 2
    middle = parameters_list[middle_index]

    def comparison(value_at_middle: float, direct_relation: bool = True):
        return (value_at_middle > 0.0) == direct_relation

    # Evaluate at the middle point
    value_at_middle = fun(middle)
    logging.debug("middle: %f value_at_middle: %f",
                  middle,
                  float(value_at_middle))

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
