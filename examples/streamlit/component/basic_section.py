import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import xarray

import enstools.compression.xr_accessor  # noqa
from .data_source import DataContainer


def get_compression_ratio(data_array: xarray.DataArray, relative_tolerance: float, mode: str) -> float:
    what = data_array.compression(f"lossy,sz,{mode},{relative_tolerance}", in_place=False)
    return float(what.attrs["compression_ratio"])


def invert_function(function):
    # Define its derivative
    f_prime = function.deriv()

    # Define the function for which we want to find the root
    def func(x, y_val):
        return function(x) - y_val

    def newtons_method(y_val, epsilon=1e-7, max_iterations=100):
        x = -2  # np.log10(0.01)
        print(f"{y_val=}")
        for _ in range(max_iterations):
            x_new = x - func(x, y_val) / f_prime(x)
            if abs(x - x_new) < epsilon:
                return x_new
            x = x_new
            print(x_new)
        return None

    return newtons_method


def create_parameter_from_compression_ratio(data: DataContainer, mode: str):
    train_x = np.logspace(-12, -.5, 15)
    train_y = [get_compression_ratio(data.reference_da, parameter, mode=mode) for parameter in train_x]

    parameter_range = min(train_y), min(100., max(train_y))

    x_log = np.log10(train_x)
    y_log = np.log10(train_y)

    coeff = np.polyfit(x_log, y_log, 10)

    # Create a polynomial function from the coefficients
    f = np.poly1d(coeff)

    f_inverse = invert_function(f)

    def function_to_return(compression_ratio: float) -> float:
        return 10 ** f_inverse(np.log10(compression_ratio))

    return parameter_range, function_to_return


def basic_section(data: DataContainer, slice_selection):
    mode = st.selectbox(label="Mode", options=["rel", "pw_rel"])
    parameter_range, get_parameter = create_parameter_from_compression_ratio(data, mode=mode)

    _min, _max = parameter_range
    options = [_min + (_max - _min) * _x for _x in np.logspace(-2, 0)]
    options = [f"{op:.2f}" for op in options]

    compression_ratio = st.select_slider(label="Compression Ratio", options=options)
    compression_ratio = float(compression_ratio)

    parameter = get_parameter(compression_ratio)

    with st.spinner():
        data.compress(f"lossy,sz,rel,{parameter}")
