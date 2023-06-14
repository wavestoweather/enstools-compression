import io
from typing import Optional

import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd

import enstools.compression.xr_accessor  # noqa
from enstools.encoding.errors import InvalidCompressionSpecification

options = ["Compression", "Analysis"]


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


def sidebar():
    with st.sidebar:
        st.title("Data selection")
        data_source = st.radio(label="Data source", options=["Tutorial Dataset", "Custom Dataset"])

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
            variable = st.selectbox(label="Variable", options=data.dataset.data_vars)
            if variable:
                data.select_variable(variable)

        slice_selection = {}
        if data.reference_da.dims and True:
            for dimension in data.reference_da.dims:
                if str(dimension) == "time":
                    if len(data.reference_da.time) > 1:
                        slice_selection[dimension] = st.select_slider(label=dimension,
                                                                      options=data.reference_da[dimension].values,
                                                                      )
                    else:
                        slice_selection[dimension] = data.reference_da.time.values[0]
                    st.markdown(f"- {dimension} -> {slice_selection[dimension]}")

                else:
                    st.markdown(f"- {dimension}")
                    _min = float(data.reference_da[dimension].values[0])
                    _max = float(data.reference_da[dimension].values[-1])


                    st.markdown(f"- {_min, _max}")
                    if _max - _min < 1000:
                        slice_selection[dimension] = st.slider(label=dimension,
                                                               min_value=_min,
                                                               max_value=_max,
                                                               value=(_min, _max),
                                                               )

            if st.button("Clear Cache"):
                st.cache_resource.clear()

        return slice_selection


@st.cache_resource
def create_data():
    return DataContainer.from_tutorial_data()


data = create_data()


def setup_main_frame():
    slice_selection = sidebar()
    st.title("enstools-compression playground")
    st.markdown("---")
    compression, analysis = st.tabs(["Compression", "Analysis"])

    with compression:
        if data.dataset is not None:
            st.markdown("# Compression")

            with st.expander("Compression Specifications"):
                specification_mode = st.radio(label="", options=["String", "Options"], horizontal=True)
                # specification, options = st.tabs(["String", "Options"])
                if specification_mode == "String":
                    compression_specification = st.text_input(label="Compression")
                elif specification_mode == "Options":
                    compressor = st.selectbox(label="Compressor", options=["sz", "zfp"])
                    if compressor == "sz":
                        mode_options = ["abs", "rel", "pw_rel"]
                    elif compressor == "zfp":
                        mode_options = ["accuracy", "rate", "precision"]
                    else:
                        mode_options = []
                    mode = st.selectbox(label="Mode", options=mode_options)
                    parameter = st.text_input(label="Parameter")

                    compression_specification = f"lossy,{compressor},{mode},{parameter}"
                    st.markdown(f"**Compression Specification:** {compression_specification}")

                if compression_specification:
                    try:
                        data.compress(compression_specification)
                    except InvalidCompressionSpecification:
                        st.warning("Invalid compression specification!")
                        st.markdown(
                            "Check [the compression specification format](https://enstools-encoding.readthedocs.io/en/latest/CompressionSpecificationFormat.html)")
                if data.compressed_da is not None:
                    st.markdown(f"**Compression Ratio**: {data.compressed_da.attrs['compression_ratio']}")

            col1, col2, *others = st.columns(2)

            new_slice = {}

            for key, values in slice_selection.items():
                if isinstance(values, tuple):
                    start, stop = values
                    if start != stop:
                        new_slice[key] = slice(start, stop)
                    else:
                        new_slice[key] = start
                else:
                    new_slice[key] = values

            slice_selection = new_slice

            if data.reference_da is not None:
                print(f"{slice_selection=}")
                slice_selection = {key: (value if key != "lat" else slice(value.stop, value.start)) for key, value in
                                   slice_selection.items()}

                only_slices = {key: value for key, value in slice_selection.items() if isinstance(value, slice)}
                non_slices = {key: value for key, value in slice_selection.items() if not isinstance(value, slice)}

                if only_slices:
                    reference_slice = data.reference_da.sel(**only_slices)
                else:
                    reference_slice = data.reference_da

                if non_slices:
                    reference_slice = reference_slice.sel(**non_slices, method="nearest")
                print(reference_slice)
                try:
                    reference_slice.plot()
                    fig1 = plt.gcf()
                    with col1:
                        st.pyplot(fig1)
                except TypeError:
                    pass

            if data.compressed_da is not None:
                plt.figure()
                if only_slices:
                    compressed_slice = data.compressed_da.sel(**only_slices)
                else:
                    compressed_slice = data.compressed_da
                if non_slices:
                    compressed_slice = compressed_slice.sel(**non_slices, method="nearest")


                try:
                    compressed_slice.plot()
                    fig2 = plt.gcf()
                    with col2:
                        st.pyplot(fig2)
                except TypeError:
                    pass

            else:
                st.text("Compress the data to show the plot!")


setup_main_frame()
