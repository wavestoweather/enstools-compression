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


def advanced_section(data, slice_selection):
    if data.dataset is not None:
        # st.markdown("# Compression")

        with st.expander("Compression Specifications"):
            specification_mode = st.radio(label="", options=["Options", "String"], horizontal=True)
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