import io
from typing import Optional

import pandas as pd
import streamlit as st
import xarray as xr


class DataContainer:
    def __init__(self, dataset: Optional[xr.Dataset] = None):
        self.dataset = dataset
        self.reference_da = None
        self.compressed_da = None

    def set_dataset(self, dataset):
        self.dataset = dataset
        self.reference_da = None
        self.compressed_da = None

    def select_variable(self, variable):
        self.reference_da = self.dataset[variable]

    @classmethod
    def from_tutorial_data(cls, dataset_name: str = "air_temperature"):
        return cls(dataset=xr.tutorial.open_dataset(dataset_name))

    @property
    def time_steps(self):
        if self.reference_da is not None:
            if "time" in self.reference_da.dims:
                try:
                    return pd.to_datetime(self.reference_da.time.values)
                except TypeError:
                    return self.reference_da.time.values

            print(self.reference_da)

    def compress(self, compression):
        self.compressed_da = self.reference_da.compression(compression)


@st.cache_resource
def create_data():
    return DataContainer.from_tutorial_data()


def select_dataset(data):
    st.title("Select Dataset")
    data_source = st.radio(label="Data source", options=["Tutorial Dataset", "Custom Dataset"])
    col1, col2 = st.columns(2)
    if data_source == "Tutorial Dataset":
        tutorial_dataset_options = [
            "air_temperature",
            "air_temperature_gradient",
            # "basin_mask",  # Different coordinates
            # "rasm",  # Has nan
            "ROMS_example",
            "tiny",
            # "era5-2mt-2019-03-uk.grib",
            "eraint_uvz",
            "ersstv5"
        ]
        with col1:
            dataset_name = st.selectbox(label="Dataset", options=tutorial_dataset_options)
        dataset = xr.tutorial.open_dataset(dataset_name)

        data.set_dataset(dataset)

    elif data_source == "Custom Dataset":
        my_file = st.file_uploader(label="Your file")
        data.set_dataset(None)

        if my_file:
            my_virtual_file = io.BytesIO(my_file.read())
            my_dataset = xr.open_dataset(my_virtual_file)
            st.text("Custom dataset loaded!")
            data.set_dataset(my_dataset)

    if data.dataset is not None:
        with col2:
            variable = st.selectbox(label="Variable", options=data.dataset.data_vars)
        if variable:
            data.select_variable(variable)


def select_slice(data):
    st.title("Select Slice")
    slice_selection = {}
    if data.reference_da is not None and data.reference_da.dims and True:

        tabs = st.tabs(tabs=data.reference_da.dims)
        for idx, dimension in enumerate(data.reference_da.dims):
            with tabs[idx]:
                if str(dimension) == "time":
                    if len(data.reference_da.time) > 1:
                        slice_selection[dimension] = st.select_slider(label=dimension,
                                                                      options=data.reference_da[dimension].values,
                                                                      )
                    else:
                        slice_selection[dimension] = data.reference_da.time.values[0]

                else:
                    _min = float(data.reference_da[dimension].values[0])
                    _max = float(data.reference_da[dimension].values[-1])

                    if _max - _min < 1000:
                        slice_selection[dimension] = st.slider(label=dimension,
                                                               min_value=_min,
                                                               max_value=_max,
                                                               value=(_min, _max),
                                                               )

        # if st.button("Clear Cache"):
        #     st.cache_resource.clear()

    return slice_selection
