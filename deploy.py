import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Laser RPM Analyzer",
    layout="wide"
)

st.title("Laser RPM Correlation Analyzer")

uploaded_file = st.file_uploader(
    "Upload Excel",
    type=["xlsx"]
)

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    cols = list(df.columns)

    laser_col = st.selectbox(
        "Laser Column",
        cols,
        index=cols.index("laser")
        if "laser" in cols
        else 0
    )

    rpm_col = st.selectbox(
        "RPM Column",
        cols,
        index=cols.index("rpm")
        if "rpm" in cols
        else 0
    )

    # ==========================================
    # SAFE NUMERIC CONVERSION
    # ==========================================

    laser_raw = pd.to_numeric(
        df[laser_col]
        .astype(str)
        .str.replace(",", "."),
        errors="coerce"
    ).dropna().to_numpy()

    rpm_raw = pd.to_numeric(
        df[rpm_col]
        .astype(str)
        .str.replace(",", "."),
        errors="coerce"
    ).dropna().to_numpy()

    if len(laser_raw) == 0:
        st.error("Laser column contains no valid numeric data")
        st.stop()

    if len(rpm_raw) == 0:
        st.error("RPM column contains no valid numeric data")
        st.stop()

    st.info(
        f"Laser Samples: {len(laser_raw)} | RPM Samples: {len(rpm_raw)}"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        laser_start = st.number_input(
            "Laser Start",
            min_value=0,
            value=0
        )

    with c2:
        laser_end = st.number_input(
            "Laser End",
            min_value=1,
            value=min(
                3000,
                len(laser_raw)
            )
        )

    with c3:
        rpm_start = st.number_input(
            "RPM Start",
            min_value=0,
            value=0
        )

    with c4:
        step = st.slider(
            "Step",
            0.30,
            1.20,
            0.61,
            0.01
        )

    use_sin35 = st.checkbox(
        "Use sin(35°)"
    )

    # ==========================================
    # CORRECTION
    # ==========================================

    laser_corrected = laser_raw.copy()

    if use_sin35:
        laser_corrected = (
            laser_corrected *
            np.sin(
                np.deg2rad(35)
            )
        )

    # ==========================================
    # NORMALIZE
    # ==========================================

    laser_norm = (
        laser_corrected -
        laser_corrected.min()
    ) / (
        laser_corrected.max() -
        laser_corrected.min()
    )

    rpm_norm = (
        rpm_raw -
        rpm_raw.min()
    ) / (
        rpm_raw.max() -
        rpm_raw.min()
    )

    # ==========================================
    # INVERT LASER
    # ==========================================

    laser_norm = 1 - laser_norm

    # ==========================================
    # CROP
    # ==========================================

    laser_crop = laser_norm[
        int(laser_start):
        int(laser_end)
    ]

    if len(laser_crop) < 5:
        st.warning(
            "Laser crop too small"
        )
        st.stop()

    # ==========================================
    # ALIGN RPM
    # ==========================================

    positions = (
        np.arange(
            len(laser_crop)
        ) * step
    )

    positions += rpm_start

    valid = (
        positions <=
        len(rpm_norm) - 1
    )

    positions = positions[valid]

    laser_final = laser_crop[
        :len(positions)
    ]

    rpm_final = np.interp(
        positions,
        np.arange(
            len(rpm_norm)
        ),
        rpm_norm
    )

    # ==========================================
    # CORRELATION
    # ==========================================

    corr = np.nan

    if len(laser_final) > 2:

        corr = np.corrcoef(
            laser_final,
            rpm_final
        )[0, 1]

    st.metric(
        "Correlation",
        f"{corr:.6f}"
    )

    # ==========================================
    # TABS
    # ==========================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "Raw Laser",
        "Corrected Laser",
        "Normalized + Inverted",
        "Alignment & Correlation"
    ])

    # ==========================================
    # TAB 1
    # ==========================================

    with tab1:

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                y=laser_raw,
                name="Raw Laser"
            )
        )

        fig.update_layout(
            title="Laser Raw"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # ==========================================
    # TAB 2
    # ==========================================

    with tab2:

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                y=laser_corrected,
                name="Corrected Laser"
            )
        )

        fig.update_layout(
            title=
            "Laser × sin(35°)"
            if use_sin35
            else
            "Laser Raw (No Correction)"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # ==========================================
    # TAB 3
    # ==========================================

    with tab3:

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                y=laser_norm,
                name="Normalized + Inverted"
            )
        )

        fig.update_layout(
            title=
            "Normalized + Inverted"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # ==========================================
    # TAB 4
    # ==========================================

    with tab4:

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=(
                "Reference Laser (Fixed)",
                "RPM (Shifted)"
            )
        )

        fig.add_trace(
            go.Scatter(
                y=laser_final,
                name="Laser"
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                y=rpm_final,
                name="RPM"
            ),
            row=2,
            col=1
        )

        fig.update_layout(
            height=800,
            title=(
                f"Correlation = {corr:.6f}"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.write(
            f"""
            Laser Range : [{laser_start}:{laser_end}]
            
            RPM Start   : {rpm_start}
            
            Step        : {step:.2f}
            
            sin(35°)    : {'ON' if use_sin35 else 'OFF'}
            """
        )