
import streamlit as st

from component.data_source import create_data, select_dataset, select_slice
from component.compression_section import compression_section, plot_compressed
from component.analysis_section import analysis_section


st.set_page_config(layout="wide")


data = create_data()


def sidebar():
    ...


def setup_main_frame():
    st.title("Lossy Compression playground!")
    # with st.expander("Data Selection"):
    with st.sidebar:
        select_dataset(data)
        slice_selection = select_slice(data)

    st.markdown("---")
    options = ["Compression", "Analysis"]
    compression, analysis = st.tabs(options)

    with compression:
        compression_section(data=data, slice_selection=slice_selection)
        with st.spinner():
            try:
                plot_compressed(data=data, slice_selection=slice_selection)
            except TypeError as err:
                st.warning(err)
    with analysis:
        analysis_section(data=data, slice_selection=slice_selection)

sidebar()
setup_main_frame()
