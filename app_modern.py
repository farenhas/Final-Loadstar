
"""
Load Forecaster Dashboard - Modern Version
ThingsBoard-inspired design with horizontal bar chart recommendations
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta, datetime, time
from pathlib import Path
import base64

# Import custom modules
from utils.db_util import get_unique_feeders, load_data_from_db
from feeders import (
    birem,
    gegger,
    labang,
    tragah,
    torjun,
    galis,
    unibang,
    alang_alang,
    alas_kembang,
    aros_baya,
    pemuda_kaffa,
    tanah_merah,
    suramadu,
    sekarbungu,
    parseh,
    tanjung_bumi,
)

# Import our new design system and components
from design_system import Colors, generate_modern_css, get_status_color
from constants import (
    FORECAST_HOURS,
    HIST_DAYS,
    MAX_CAPACITY,
    WARNING_THRESHOLD,
    FEEDER_PAIRS,
    LOGO_PATH,
    SECTION_TITLES,
)
from chart_components import (
    create_recommendation_bar_chart,
    create_partner_forecast_chart,
    create_main_forecast_chart,
    create_realtime_chart,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Load Monitor & Forecast System",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# LOGO HANDLING
# ============================================================
def get_base64_logo(img_path: Path) -> str:
    """Convert logo to base64 for embedding"""
    try:
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""


logo_base64 = get_base64_logo(LOGO_PATH) if LOGO_PATH and LOGO_PATH.exists() else ""


# ============================================================
# INJECT MODERN CSS
# ============================================================
st.markdown(generate_modern_css(logo_base64), unsafe_allow_html=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def normalize_forecast_df(fc):
    """Normalize forecast dataframe columns"""
    if fc is None:
        return None
    df = fc.copy()

    # Normalize datetime column
    if "datetime" not in df.columns:
        for alt in ["timestamp", "ds", "date"]:
            if alt in df.columns:
                df = df.rename(columns={alt: "datetime"})
                break
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    # Normalize forecast column
    if "forecast" not in df.columns:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if num_cols:
            df = df.rename(columns={num_cols[0]: "forecast"})
        else:
            return None

    return df.dropna().sort_values("datetime").reset_index(drop=True)


def call_forecast_module(name, historical_df, start_datetime=None):
    """Call appropriate forecast module for feeder"""
    if historical_df is None or historical_df.empty:
        return None

    name = name.lower()

    module_map = {
        "birem": birem,
        "gegger": gegger,
        "labang": labang,
        "tragah": tragah,
        "torjun": torjun,
        "galis": galis,
        "unibang": unibang,
        "alas kembang": alas_kembang,
        "alang-alang": alang_alang,
        "pemuda kaffa": pemuda_kaffa,
        "aros baya": aros_baya,
        "sekarbungu": sekarbungu,
        "tanah merah": tanah_merah,
        "suramadu": suramadu,
        "tanjung bumi": tanjung_bumi,
        "parseh": parseh,
    }

    module = module_map.get(name)
    if not module:
        return None

    try:
        raw_fc = module.forecast(
            historical_df.set_index("timestamp"),
            steps=FORECAST_HOURS,
            start_datetime=start_datetime,
        )
        return normalize_forecast_df(raw_fc)
    except Exception as e:
        st.error(f"Error model '{name}': {e}")
        return None


def resample_to_hourly(df, datetime_col="datetime", value_col="forecast"):
    """Resample data to hourly frequency"""
    if df is None or df.empty:
        return None
    df = df.copy()
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df = df.set_index(datetime_col)
    df_hourly = df[value_col].resample("H").mean().reset_index()
    df_hourly.columns = [datetime_col, value_col]
    return df_hourly


def generate_hour_options():
    """Generate hourly time options from 00:00 to 23:00"""
    return [time(h, 0) for h in range(24)]


# ============================================================
# FILTER SECTION
# ============================================================
unique_feeders = get_unique_feeders()
if not unique_feeders:
    st.error("❌ Tidak ada feeder ditemukan di database.")
    st.stop()

st.markdown('<div class="filter-container">', unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

hour_options = generate_hour_options()

with col1:
    selected_feeder = st.selectbox("Penyulang Asal", unique_feeders)
with col2:
    start_date = st.date_input("Tanggal Mulai")
with col3:
    start_time = st.selectbox(
        "Jam Mulai", hour_options, index=0, format_func=lambda x: x.strftime("%H:%M")
    )
with col4:
    end_date = st.date_input("Tanggal Selesai")
with col5:
    end_time = st.selectbox(
        "Jam Selesai",
        hour_options,
        index=23,
        format_func=lambda x: x.strftime("%H:%M"),
    )

st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# MAIN PROCESSING
# ============================================================
partner_results = []

if selected_feeder and start_date and end_date:
    # Load historical data
    df_hist = load_data_from_db(selected_feeder)
    if df_hist.empty:
        st.error("Data historis tidak ditemukan untuk feeder ini.")
        st.stop()

    # Data preprocessing
    df_hist["arus"] = pd.to_numeric(df_hist["arus"], errors="coerce")
    df_hist.dropna(subset=["arus"], inplace=True)
    df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])

    last_data_time = df_hist["timestamp"].max()
    period_start = pd.to_datetime(datetime.combine(start_date, start_time))
    period_end = pd.to_datetime(datetime.combine(end_date, end_time))

    # Validation
    if period_end <= period_start:
        st.error("Tanggal atau jam selesai harus lebih besar dari waktu mulai.")
        st.stop()

    if period_end > (last_data_time + timedelta(hours=FORECAST_HOURS)):
        st.error(f"Periode melebihi jangkauan forecast ({FORECAST_HOURS} jam).")
        st.stop()

    # Subset historical data for display
    df_hist_display = df_hist[
        df_hist["timestamp"] >= (last_data_time - timedelta(days=HIST_DAYS))
    ].copy()

    # Forecast main feeder
    fc_main = call_forecast_module(selected_feeder, df_hist)
    if fc_main is None or fc_main.empty:
        st.warning(f"⚠ Feeder '{selected_feeder}' belum memiliki model forecast.")
        st.stop()

    # Normalize and resample
    if "datetime" in fc_main.columns:
        fc_main = fc_main.rename(columns={"datetime": "timestamp"})
    fc_main["timestamp"] = pd.to_datetime(fc_main["timestamp"])
    fc_main_hourly = resample_to_hourly(fc_main, "timestamp", "forecast")

    # Filter by user period
    fc_filtered = fc_main_hourly[
        (fc_main_hourly["timestamp"] >= period_start)
        & (fc_main_hourly["timestamp"] <= period_end)
    ].copy()

    # ========================================================
    # ROW 1: REKOMENDASI (BAR CHART) + PREDIKSI MANUVER (2x2)
    # ========================================================
    col_left, col_right = st.columns([2, 1])

    # ========================================================
    # KOLOM KANAN: REKOMENDASI MANUVER (BAR CHART)
    # ========================================================
    with col_right:
        # Get partner feeders
        partner_list = FEEDER_PAIRS.get(selected_feeder.lower(), [])

        if partner_list:
            for partner in partner_list:
                try:
                    df_partner = load_data_from_db(partner)
                    if df_partner.empty:
                        continue

                    # Preprocessing
                    df_partner["arus"] = pd.to_numeric(
                        df_partner["arus"], errors="coerce"
                    )
                    df_partner.dropna(subset=["arus"], inplace=True)
                    df_partner["timestamp"] = pd.to_datetime(df_partner["timestamp"])

                    # Forecast partner
                    fc_partner = call_forecast_module(partner, df_partner)
                    if fc_partner is None or fc_partner.empty:
                        continue

                    # Normalize
                    if "datetime" in fc_partner.columns:
                        fc_partner = fc_partner.rename(
                            columns={"datetime": "timestamp"}
                        )
                    fc_partner["timestamp"] = pd.to_datetime(fc_partner["timestamp"])

                    # Resample
                    fc_partner_hourly = resample_to_hourly(
                        fc_partner, "timestamp", "forecast"
                    )
                    if fc_partner_hourly is None or fc_partner_hourly.empty:
                        continue

                    # Filter by period
                    fc_partner_filtered = fc_partner_hourly[
                        (fc_partner_hourly["timestamp"] >= period_start)
                        & (fc_partner_hourly["timestamp"] <= period_end)
                    ].copy()

                    if fc_partner_filtered.empty:
                        continue

                    # Merge and calculate total
                    merged = pd.merge(
                        fc_filtered,
                        fc_partner_filtered,
                        on="timestamp",
                        suffixes=("_main", "_partner"),
                    )

                    if merged.empty:
                        continue

                    merged["total_transfer"] = (
                        merged["forecast_main"] + merged["forecast_partner"]
                    )
                    max_load = round(merged["total_transfer"].max(), 2)

                    # Determine status
                    status, color, label = get_status_color(
                        max_load, WARNING_THRESHOLD, MAX_CAPACITY
                    )

                    # Store results
                    partner_results.append(
                        (partner, max_load, status, label, fc_partner_filtered)
                    )

                except Exception as e:
                    continue

        st.markdown(
            f"""
            <div class="recommendation-container">
                <div class="recommendation-header">{SECTION_TITLES["recommendations"]}</div>
                <div class="recommendation-body">
            """,
            unsafe_allow_html=True,
        )

        # Chart atau pesan kosong
        if partner_results:
            fig_rec = create_recommendation_bar_chart(partner_results)
            st.plotly_chart(
                fig_rec, 
                use_container_width=True, 
                config={"displayModeBar": False}
            )
        else:
            st.markdown(
                '<p style="text-align: center; color: #9ca3af; padding: 2rem 0;">Tidak ada rekomendasi untuk periode ini</p>',
                unsafe_allow_html=True,
            )

        # Tutup div
        st.markdown("</div></div>", unsafe_allow_html=True)

    # ========================================================
    # KOLOM KIRI: PREDIKSI MANUVER (2x2 GRID)
    # ========================================================
    with col_left:
        if partner_results:
            st.markdown(
                f'<div class="card-modern"><div class="card-header-modern">{SECTION_TITLES["maneuver_forecast"]}</div></div>',
                unsafe_allow_html=True,
            )

            cols = st.columns(2)
            for idx, (partner, max_load, status, label, df_fc) in enumerate(
                partner_results
            ):
                with cols[idx % 2]:
                    fig_partner = create_partner_forecast_chart(
                        partner, fc_filtered, df_fc, status, max_load
                    )
                    st.plotly_chart(
                        fig_partner,
                        use_container_width=True,
                        config={"displayModeBar": False},
                    )

    # ========================================================
    # ROW 2: PREDIKSI 72 JAM + TABEL RINCIAN
    # ========================================================
    col_chart, col_table = st.columns([2, 1])

    with col_chart:
        st.markdown(
            f'<div class="card-modern"><div class="card-header-modern">{SECTION_TITLES["forecast_72h"]}</div></div>',
            unsafe_allow_html=True,
        )

        if not fc_filtered.empty:
            fig_main = create_main_forecast_chart(fc_filtered, selected_feeder)
            st.plotly_chart(
                fig_main, use_container_width=True, config={"displayModeBar": False}
            )
        else:
            st.warning("⚠ Tidak ada data forecast dalam rentang tanggal yang dipilih.")

    with col_table:
        if not fc_filtered.empty:
            table_html = (
            f'<div class="card-header-modern" style="margin-bottom: 1rem;">{SECTION_TITLES["detail_table"]}</div>'
            '<div class="data-table"><table>'
            '<thead><tr><th>Waktu</th><th>Arus (A)</th></tr></thead><tbody>'
        )

            for _, row in fc_filtered.iterrows():
                dt = row["timestamp"]
                forecast_val = round(row["forecast"], 2)
                time_str = dt.strftime("%d %b %H:%M")

                # Determine status badge
                if forecast_val < WARNING_THRESHOLD:
                    status_badge = '<span class="status-badge badge-safe">AMAN</span>'
                    load_class = "low-load"
                elif forecast_val < MAX_CAPACITY:
                    status_badge = (
                        '<span class="status-badge badge-warning">WARNING</span>'
                    )
                    load_class = "medium-load"
                else:
                    status_badge = (
                        '<span class="status-badge badge-danger">BAHAYA</span>'
                    )
                    load_class = "high-load"

                table_html += (
                    f"<tr>"
                    f"<td>{time_str}</td>"
                    f'<td class="{load_class}">{forecast_val}</td>'
                    f"</tr>"
                )

            table_html += "</tbody></table></div></div></div>"
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="card-modern">'
                f'<div class="card-header-modern">{SECTION_TITLES["detail_table"]}</div>'
                '<div class="card-body-modern">'
                '<p style="text-align: center; color: #9ca3af;">Tidak ada data untuk ditampilkan</p>'
                "</div></div>",
                unsafe_allow_html=True,
            )

    # ========================================================
    # ROW 3: BEBAN REAL-TIME
    # ========================================================
    st.markdown(
        f'<div class="card-modern"><div class="card-header-modern">{SECTION_TITLES["realtime"]}</div></div>',
        unsafe_allow_html=True,
    )

    if not df_hist_display.empty:
        fig_realtime = create_realtime_chart(df_hist_display, selected_feeder)
        st.plotly_chart(
            fig_realtime, use_container_width=True, config={"displayModeBar": False}
        )
    else:
        st.warning("⚠ Tidak ada data real-time untuk ditampilkan.")


# ============================================================
# FOOTER INFO (Optional)
# ============================================================
st.markdown(
    """
    <div style="text-align: center; padding: 2rem 0 1rem 0; color: #9ca3af; font-size: 0.8rem;">
        <p style="margin: 0;">Load Forecaster Dashboard v2.0 - Modern Edition</p>
        <p style="margin: 0.25rem 0 0 0;">Powered by Streamlit & Plotly</p>
    </div>
    """,
    unsafe_allow_html=True,
)
