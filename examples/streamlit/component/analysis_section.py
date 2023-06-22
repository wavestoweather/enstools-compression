import streamlit as st

import enstools.compression.xr_accessor  # noqa


def analysis_section(data, slice_selection):
    if data.dataset is not None:
        # st.markdown("# Compression")
        col1, col2 = st.columns(2)
        with col1:
            constrains = st.text_input(label="Constraint", value="correlation_I:5,ssim_I:3")

        options = {
            "sz": ["abs", "rel", "pw_rel"],
            "sz3": ["abs", "rel"],
            "zfp": ["accuracy", "rate", "precision"],
        }

        all_options = []
        [all_options.extend([f"{compressor}-{mode}" for mode in options[compressor]]) for compressor in options]

        with col2:
            cases = st.multiselect(label="Compressor and mode", options=all_options)

        if data.reference_da is None:
            return

        if not cases:
            return

        st.markdown("# Results:")
        n_cols = 4
        cols = st.columns(n_cols)

        all_results = {}

        for idx, case in enumerate(cases):
            with cols[idx % n_cols]:
                compressor, mode = case.split("-")
                encoding, metrics = data.reference_da.compression.analyze(
                    constrains=constrains,
                    compressor=compressor,
                    compression_mode=mode
                )
                parameter = encoding.split(",")[-1]
                compression_ratio = metrics["compression_ratio"]
                all_results[case] = compression_ratio
                st.markdown(f"## {compressor},{mode}:\n\n"
                            f"**Compression Ratio:** {compression_ratio:.2f}x\n\n"
                            f"**Parameter:** {parameter}\n\n"
                            f"**Specification String:**")
                st.code(encoding)
                st.markdown(f"___")
                # st.markdown(encoding)
                # st.markdown(metrics)
