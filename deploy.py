from io import BytesIO

from openpyxl import Workbook

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

    c1, c2, c3= st.columns(4)

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
    if "laser_final_hold" not in st.session_state:
        st.session_state.laser_final_hold = None
        st.session_state.rpm_final_hold = None
        st.session_state.corr_hold = None
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

    invert_laser = st.checkbox(
        "Invert Laser",
        value=True
    )
    hold_graph = st.checkbox(
        "Hold Graph",
        value=False
    )
    if invert_laser:
        laser_norm = 1 - laser_norm

    laser_crop = laser_norm[
        int(laser_start):
        int(laser_end)
    ]

    if len(laser_crop) < 5:
        st.warning(
            "Laser crop too small"
        )
        st.stop()

    corr = np.nan

    if len(laser_final) > 2:

        corr = np.corrcoef(
            laser_final,
            rpm_final
        )[0, 1]

    if not hold_graph:

        st.session_state.laser_final_hold = laser_final.copy()
        st.session_state.rpm_final_hold = rpm_final.copy()
        st.session_state.corr_hold = corr

    else:

        if st.session_state.laser_final_hold is not None:

            laser_final = st.session_state.laser_final_hold
            rpm_final = st.session_state.rpm_final_hold
            corr = st.session_state.corr_hold
    st.metric(
        "Correlation",
        f"{corr:.6f}"
    )
    if corr > 0:
        st.success("Positive Correlation")
    else:
        st.error("Negative Correlation")
    if "laser_high_hold" not in st.session_state:
        st.session_state.laser_high_hold = None
        st.session_state.rpm_high_hold = None
        st.session_state.high_corr_hold = None

    if "laser_low_hold" not in st.session_state:
        st.session_state.laser_low_hold = None
        st.session_state.rpm_low_hold = None
        st.session_state.low_corr_hold = None

    tab1, tab2, tab3, tab4 = st.tabs([
        "Raw Laser",
        "Corrected Laser",
        "Normalized + Inverted",
        "Alignment & Correlation"
    ])

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

    with tab4:

        st.subheader(
            f"Global Correlation = {corr:.6f}"
        )

        step = st.slider(
            "Step",
            0.30,
            1.20,
            0.61,
            0.01,
            key="step_slider"
        )
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
        if "laser_final_hold" not in st.session_state:
            st.session_state.laser_final_hold = None
            st.session_state.rpm_final_hold = None
            st.session_state.corr_hold = None
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

        st.divider()
        st.subheader("High Wave")

        high_range = st.slider(
            "Select High Wave",
            0,
            len(laser_final)-1,
            (100, 600),
            key="high"
        )
        hold_high = st.checkbox(
            "Hold High Wave",
            key="hold_high"
        )

        hs, he = high_range

        laser_high = laser_final[hs:he]
        rpm_high = rpm_final[hs:he]

        high_corr = np.nan

        if len(laser_high) > 2:
            high_corr = np.corrcoef(
                laser_high,
                rpm_high
            )[0,1]
        if not hold_high:

            st.session_state.laser_high_hold = laser_high.copy()
            st.session_state.rpm_high_hold = rpm_high.copy()
            st.session_state.high_corr_hold = high_corr

        else:

            if st.session_state.laser_high_hold is not None:

                laser_high = st.session_state.laser_high_hold
                rpm_high = st.session_state.rpm_high_hold
                high_corr = st.session_state.high_corr_hold
        st.subheader(
            f"High Wave Correlation = {high_corr:.6f}"
        )

        fig_high = go.Figure()

        fig_high.add_trace(
            go.Scatter(
                y=laser_high,
                name="Laser"
            )
        )

        fig_high.add_trace(
            go.Scatter(
                y=rpm_high,
                name="RPM"
            )
        )

        fig_high.update_layout(
            title=f"High Wave [{hs}:{he}]"
        )

        st.plotly_chart(
            fig_high,
            use_container_width=True
        )
        high_png = BytesIO()


        high_png.seek(0)
        st.divider()
        st.subheader("Low Wave")

        low_range = st.slider(
            "Select Low Wave",
            0,
            len(laser_final)-1,
            (800, 1200),
            key="low"
        )
        ls, le = low_range

        laser_low = laser_final[ls:le]
        rpm_low = rpm_final[ls:le]

        low_corr = np.nan

        if len(laser_low) > 2:
            low_corr = np.corrcoef(
                laser_low,
                rpm_low
            )[0,1]
        hold_low = st.checkbox(
            "Hold Low Wave",
            key="hold_low"
        )
        if not hold_low:

            st.session_state.laser_low_hold = laser_low.copy()
            st.session_state.rpm_low_hold = rpm_low.copy()
            st.session_state.low_corr_hold = low_corr

        else:

            if st.session_state.laser_low_hold is not None:

                laser_low = st.session_state.laser_low_hold
                rpm_low = st.session_state.rpm_low_hold
                low_corr = st.session_state.low_corr_hold
        st.subheader(
            f"Low Wave Correlation = {low_corr:.6f}"
        )

        fig_low = go.Figure()

        fig_low.add_trace(
            go.Scatter(
                y=laser_low,
                name="Laser"
            )
        )

        fig_low.add_trace(
            go.Scatter(
                y=rpm_low,
                name="RPM"
            )
        )

        fig_low.update_layout(
            title=f"Low Wave [{ls}:{le}]"
        )

        st.plotly_chart(
            fig_low,
            use_container_width=True
        )
        low_png = BytesIO()

        low_png.seek(0)
        st.divider()

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            pd.DataFrame({
                "Metric": [
                    "Global Correlation",
                    "High Wave Correlation",
                    "Low Wave Correlation"
                ],
                "Value": [
                    corr,
                    high_corr,
                    low_corr
                ]
            }).to_excel(
                writer,
                sheet_name="Summary",
                index=False
            )

            pd.DataFrame({
                "laser": laser_high,
                "rpm": rpm_high
            }).to_excel(
                writer,
                sheet_name="High Wave",
                index=False
            )

            pd.DataFrame({
                "laser": laser_low,
                "rpm": rpm_low
            }).to_excel(
                writer,
                sheet_name="Low Wave",
                index=False
            )

        output.seek(0)

        st.download_button(
            label="Download XLSX Report",
            data=output,
            file_name="laser_rpm_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )