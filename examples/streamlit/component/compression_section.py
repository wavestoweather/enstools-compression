import matplotlib.pyplot as plt
import streamlit as st

import enstools.compression.xr_accessor  # noqa
from enstools.encoding.errors import InvalidCompressionSpecification

default_parameters = {
    "sz": {
        "abs": 1,
        "rel": 0.001,
        "pw_rel": 0.001,
    },
    "sz3": {
        "abs": 1,
        "rel": 0.001,
    },
    "zfp": {
        "accuracy": 1,
        "rate": 3.2,
        "precision": 14,
    }

}


def compression_section(data, slice_selection):
    if data.dataset is not None:
        # st.markdown("# Compression")

        with st.expander("Compression Specifications"):
            specification_mode = st.radio(label="", options=["String", "Options"], horizontal=True)
            # specification, options = st.tabs(["String", "Options"])
            if specification_mode == "String":
                compression_specification = st.text_input(label="Compression", value="lossy,sz,abs,1")
            elif specification_mode == "Options":
                col1_, col2_, col3_ = st.columns(3)
                with col1_:
                    compressor = st.selectbox(label="Compressor", options=["sz", "sz3", "zfp"])
                if compressor == "sz":
                    mode_options = ["abs", "rel", "pw_rel"]
                elif compressor == "sz3":
                    mode_options = ["abs", "rel"]
                elif compressor == "zfp":
                    mode_options = ["accuracy", "rate", "precision"]
                else:
                    mode_options = []
                with col2_:
                    mode = st.selectbox(label="Mode", options=mode_options)
                with col3_:
                    parameter = st.text_input(label="Parameter", value=default_parameters[compressor][mode])

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


def plot_compressed(data, slice_selection):
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
