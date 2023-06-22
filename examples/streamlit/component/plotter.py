import streamlit as st
import matplotlib.pyplot as plt

def plot_comparison(data, slice_selection):
    col1, col2, col3, *others = st.columns(3)

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

        diff = data.compressed_da - data.reference_da
        plt.figure()
        if only_slices:
            diff_slice = diff.sel(**only_slices)
        else:
            diff_slice = data.compressed_da
        if non_slices:
            diff_slice = diff_slice.sel(**non_slices, method="nearest")

        try:
            diff_slice.plot()
            fig3 = plt.gcf()
            with col3:
                st.pyplot(fig3)
        except TypeError:
            pass




    else:
        st.text("Compress the data to show the plot!")
