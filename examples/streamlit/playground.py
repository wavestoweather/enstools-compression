import streamlit as st

from component.data_source import create_data, select_dataset, select_slice
from component.basic_section import basic_section
from component.advanced_section import advanced_section
from component.analysis_section import analysis_section
from component.plotter import plot_comparison

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")


data = create_data()


def setup_main_frame():
    st.title("Welcome to the :green[enstools-compression] playground!")
    with st.sidebar:
        select_dataset(data)
        slice_selection = select_slice(data)

    st.markdown("---")
    options = ["Compression", "Advanced Compression", "Analysis"]
    basic, advanced, analysis = st.tabs(options)

    with basic:
        basic_section(data=data, slice_selection=slice_selection)
        with st.spinner():
            try:
                plot_comparison(data=data, slice_selection=slice_selection)
            except TypeError as err:
                st.warning(err)

    with advanced:
        advanced_section(data=data, slice_selection=slice_selection)
        with st.spinner():
            try:
                plot_comparison(data=data, slice_selection=slice_selection)
            except TypeError as err:
                st.warning(err)
    with analysis:
        analysis_section(data=data, slice_selection=slice_selection)


setup_main_frame()
