import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
import plotly.graph_objects as go

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
        if "laser" in cols else 0
    )

    rpm_col = st.selectbox(
        "RPM Column",
        cols,
        index=cols.index("rpm")
        if "rpm" in cols else 0
    )

    laser_raw = (
        df[laser_col]
        .dropna()
        .to_numpy(dtype=float)
    )

    rpm_raw = (
        df[rpm_col]
        .dropna()
        .to_numpy(dtype=float)
    )

    st.write(
        f"Laser Samples: {len(laser_raw)}"
    )

    st.write(
        f"RPM Samples: {len(rpm_raw)}"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        laser_start = st.number_input(
            "Laser Start",
            value=0
        )

    with c2:
        laser_end = st.number_input(
            "Laser End",
            value=min(
                3000,
                len(laser_raw)
            )
        )

    with c3:
        rpm_start = st.number_input(
            "RPM Start",
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

    laser_corrected = laser_raw.copy()

    if use_sin35:

        laser_corrected = (
            laser_corrected *
            np.sin(
                np.deg2rad(35)
            )
        )

    laser = laser_corrected.copy()

    laser = (
        laser - laser.min()
    ) / (
        laser.max() - laser.min()
    )

    rpm = (
        rpm_raw - rpm_raw.min()
    ) / (
        rpm_raw.max() - rpm_raw.min()
    )

    laser = 1 - laser

    laser_crop = laser[
        int(laser_start):
        int(laser_end)
    ]

    positions = (
        np.arange(
            len(laser_crop)
        ) * step
    )

    positions += rpm_start

    valid = (
        positions <=
        (len(rpm) - 1)
    )

    positions = positions[valid]

    laser_final = laser_crop[
        :len(positions)
    ]

    rpm_final = np.interp(
        positions,
        np.arange(len(rpm)),
        rpm
    )

    corr = np.nan

    if len(laser_final) > 2:

        corr, _ = pearsonr(
            laser_final,
            rpm_final
        )

    st.metric(
        "Correlation",
        f"{corr:.4f}"
    )

    tab1, tab2, tab3 = st.tabs([
        "Raw Laser",
        "Corrected Laser",
        "Overlay"
    ])

    with tab1:

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                y=laser_raw,
                name="Laser Raw"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with tab2:

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                y=laser_corrected,
                name="Corrected"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with tab3:

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                y=laser_final,
                name="Laser"
            )
        )

        fig.add_trace(
            go.Scatter(
                y=rpm_final,
                name="RPM"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )