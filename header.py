
# app.py - Load Monitoring Dashboard
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Utils
from utils.db_util import get_unique_feeders, load_data_from_db

# Forecast modules
from feeders import birem, gegger, labang, tragah

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Load Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS untuk styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 32px;
        font-weight: bold;
        color: #1e3a8a;
        margin-bottom: 20px;
    }
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Header dengan logo
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image(
        "https://via.placeholder.com/80x80?text=LOADSTAR", width=80
    )  # Ganti dengan path logo Anda
with col_title:
    st.markdown(
        '<div class="main-header">Load Monitoring Dashboard</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

FORECAST_HOURS = 72
MAX_CAPACITY = 320.0  # Disesuaikan dengan UI (batas normal)
WARNING_THRESHOLD = 300.0  # Threshold "Mendekati Batas"
HIST_DAYS = 7

# ============================================================
# FEEDER RELATIONS (Bidirectional)
# ============================================================
feeder_pairs = {
    "aros baya": ["pemuda kaffa", "tanjung bumi", "gegger"],
    "suramadu": ["pemuda kaffa", "parseh"],
    "labang": ["sekarbung", "tragah", "galis", "alas kembang"],
    "tragah": ["tanah merah", "labang", "alang-alang"],
    "alang-alang": ["tragah"],
    "parseh": ["suramadu", "unibang"],
    "tanah merah": ["tragah", "alas kembang", "tanjung bumi", "torjun"],
    "tanjung bumi": ["tanah merah", "birem", "alas kembang"],
    "alas kembang": ["tragah", "tanah merah", "gegger"],
    "gegger": ["aros baya", "alas kembang"],
    "pemuda kaffa": ["suramadu"],
    "galis": ["labang", "torjun"],
    "birem": ["tanjung bumi"],
    "torjun": ["tanah merah", "galis"],
    "unibang": ["parseh"],
    "sekarbung": ["labang"],
}

# Normalisasi ke lowercase dan buat bidirectional
for asal, tujuan_list in list(feeder_pairs.items()):
    for tujuan in tujuan_list:
        feeder_pairs.setdefault(tujuan.lower(), [])
        if asal.lower() not in feeder_pairs[tujuan.lower()]:
            feeder_pairs[tujuan.lower()].append(asal.lower())
feeder_pairs = {k.lower(): [t.lower() for t in v] for k, v in feeder_pairs.items()}

# ============================================================
# FORECAST FUNCTION MAPPING
# ============================================================
forecast_functions = {
    "birem": birem.forecast_birem,
    "gegger": gegger.forecast_gegger,
    "labang": labang.forecast_labang,
    "tragah": tragah.forecast_tragah,
}


def get_forecast_function(feeder_name):
    """Get appropriate forecast function for feeder"""
    feeder_lower = feeder_name.lower()
    if feeder_lower in forecast_functions:
        return forecast_functions[feeder_lower]
    # Default forecast function jika tidak ada spesifik
    return None


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def calculate_safety_status(target_load, pair_load):
    """Calculate safety status based on combined load"""
    total_load = target_load + pair_load

    if total_load < WARNING_THRESHOLD:
        return "Aman", "🟢"
    elif WARNING_THRESHOLD <= total_load <= MAX_CAPACITY:
        return "Mendekati Batas", "🟡"
    else:
        return "Tidak Aman", "🔴"


def perform_forecast(feeder_name, last_date):
    """Perform 72-hour forecast for a feeder"""
    forecast_func = get_forecast_function(feeder_name)

    if forecast_func is None:
        # Default simple forecast jika tidak ada model spesifik
        # Load data historis
        hist_data = load_data_from_db(
            feeder_name, last_date - timedelta(days=30), last_date
        )
        if hist_data.empty:
            return pd.DataFrame()

        # Simple average-based forecast
        avg_pattern = hist_data.groupby(hist_data["timestamp"].dt.hour)["arus"].mean()

        forecast_dates = pd.date_range(
            start=last_date + timedelta(hours=1), periods=FORECAST_HOURS, freq="H"
        )

        forecast_values = [
            avg_pattern.get(dt.hour, hist_data["arus"].mean()) for dt in forecast_dates
        ]

        return pd.DataFrame(
            {"timestamp": forecast_dates, "arus_forecast": forecast_values}
        )
    else:
        # Use specific forecast function
        return forecast_func(last_date)


def plot_historical_data(df, feeder_name):
    """Plot 7 days historical data"""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["arus"],
            mode="lines",
            name="Beban Real-Time",
            line=dict(color="#2563eb", width=2),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.1)",
        )
    )

    fig.update_layout(
        title=f"Beban Real-Time - {feeder_name.title()}",
        xaxis_title="",
        yaxis_title="Arus (A)",
        hovermode="x unified",
        plot_bgcolor="white",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#e5e7eb")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#e5e7eb")

    return fig


def plot_forecast_data(df, feeder_name, show_threshold=True):
    """Plot forecast data with threshold line"""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["arus_forecast"],
            mode="lines",
            name="Prediksi Beban",
            line=dict(color="#2563eb", width=2),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.1)",
        )
    )

    if show_threshold:
        fig.add_hline(
            y=MAX_CAPACITY,
            line_dash="dash",
            line_color="gray",
            annotation_text="Batas Normal",
            annotation_position="right",
        )

    fig.update_layout(
        title=f"Prediksi Beban 72 Jam ke Depan - {feeder_name.title()}",
        xaxis_title="",
        yaxis_title="Arus (A)",
        hovermode="x unified",
        plot_bgcolor="white",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#e5e7eb")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#e5e7eb", range=[0, 300])

    return fig


# ============================================================
# MAIN APP
# ============================================================

# Input Section
col1, col2, col3 = st.columns(3)

with col1:
    # Get available feeders from database
    available_feeders = get_unique_feeders()
    selected_feeder = st.selectbox(
        "Select Feeder",
        options=[""] + available_feeders,
        format_func=lambda x: x.title() if x else "Select Feeder",
    )

with col2:
    start_date = st.date_input(
        "Tanggal Mulai Pekerjaan",
        value=datetime.now().date(),
        min_value=datetime.now().date(),
    )

with col3:
    end_date = st.date_input(
        "Tanggal Selesai Pekerjaan",
        value=datetime.now().date() + timedelta(days=1),
        min_value=datetime.now().date(),
    )

st.markdown("---")

# ============================================================
# PROCESSING AND DISPLAY
# ============================================================

if selected_feeder:
    feeder_lower = selected_feeder.lower()

    # Get last date from database
    last_date = datetime.now()  # Atau ambil dari database

    # Load historical data (7 days)
    hist_start = last_date - timedelta(days=HIST_DAYS)
    hist_data = load_data_from_db(selected_feeder, hist_start, last_date)

    # Perform forecast
    with st.spinner("Melakukan forecast..."):
        target_forecast = perform_forecast(selected_feeder, last_date)

    # Get pair feeders
    pair_feeders = feeder_pairs.get(feeder_lower, [])

    # Layout: Historical + Recommendations
    col_left, col_right = st.columns([2, 1])

    with col_left:
        if not hist_data.empty:
            st.plotly_chart(
                plot_historical_data(hist_data, selected_feeder),
                use_container_width=True,
            )
        else:
            st.warning("Tidak ada data historis tersedia")

    with col_right:
        st.markdown("### Rekomendasi Manuver")

        if not target_forecast.empty and pair_feeders:
            recommendations = []

            for pair_feeder in pair_feeders:
                # Forecast pair feeder
                pair_forecast = perform_forecast(pair_feeder, last_date)

                if not pair_forecast.empty:
                    # Filter forecast berdasarkan tanggal pekerjaan
                    work_start = pd.Timestamp(start_date)
                    work_end = pd.Timestamp(end_date) + timedelta(days=1)

                    target_work = target_forecast[
                        (target_forecast["timestamp"] >= work_start)
                        & (target_forecast["timestamp"] < work_end)
                    ]
                    pair_work = pair_forecast[
                        (pair_forecast["timestamp"] >= work_start)
                        & (pair_forecast["timestamp"] < work_end)
                    ]

                    if not target_work.empty and not pair_work.empty:
                        # Merge data
                        merged = pd.merge(
                            target_work[["timestamp", "arus_forecast"]],
                            pair_work[["timestamp", "arus_forecast"]],
                            on="timestamp",
                            suffixes=("_target", "_pair"),
                        )

                        merged["total_load"] = (
                            merged["arus_forecast_target"]
                            + merged["arus_forecast_pair"]
                        )

                        # Hitung persentase status
                        total_hours = len(merged)
                        safe_hours = len(
                            merged[merged["total_load"] < WARNING_THRESHOLD]
                        )
                        warning_hours = len(
                            merged[
                                (merged["total_load"] >= WARNING_THRESHOLD)
                                & (merged["total_load"] <= MAX_CAPACITY)
                            ]
                        )
                        unsafe_hours = len(merged[merged["total_load"] > MAX_CAPACITY])

                        # Tentukan status overall
                        if unsafe_hours > 0:
                            status = "Tidak Aman"
                            icon = "🔴"
                            color = "#ef4444"
                        elif (
                            warning_hours > total_hours * 0.3
                        ):  # Lebih dari 30% dalam warning
                            status = "Mendekati Batas"
                            icon = "🟡"
                            color = "#f59e0b"
                        else:
                            status = "Aman"
                            icon = "🟢"
                            color = "#10b981"

                        recommendations.append(
                            {
                                "feeder": pair_feeder,
                                "status": status,
                                "icon": icon,
                                "color": color,
                                "safe_pct": (safe_hours / total_hours) * 100,
                                "warning_pct": (warning_hours / total_hours) * 100,
                                "unsafe_pct": (unsafe_hours / total_hours) * 100,
                            }
                        )

            # Sort: Aman first, then Mendekati Batas, then Tidak Aman
            status_order = {"Aman": 1, "Mendekati Batas": 2, "Tidak Aman": 3}
            recommendations.sort(key=lambda x: status_order[x["status"]])

            # Display recommendations
            for rec in recommendations:
                st.markdown(
                    f"""
                <div style='padding: 12px; margin: 8px 0; border-radius: 8px; 
                     border-left: 4px solid {rec['color']}; background-color: #f9fafb;'>
                    <div style='display: flex; align-items: center;'>
                        <span style='font-size: 24px; margin-right: 12px;'>{rec['icon']}</span>
                        <span style='font-weight: 500; font-size: 16px;'>{rec['feeder'].title()}</span>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("Pilih feeder untuk melihat rekomendasi")

    st.markdown("---")

    # Forecast Charts Section
    if not target_forecast.empty:
        st.markdown("### Prediksi Beban 72 Jam ke Depan")

        # Filter by work dates
        work_start = pd.Timestamp(start_date)
        work_end = pd.Timestamp(end_date) + timedelta(days=1)

        target_filtered = target_forecast[
            (target_forecast["timestamp"] >= work_start)
            & (target_forecast["timestamp"] < work_end)
        ]

        if not target_filtered.empty:
            # Display forecasts in columns
            num_pairs = min(
                len(pair_feeders), 2
            )  # Max 3 charts per row (target + 2 pairs)
            cols = st.columns(num_pairs + 1)

            # Target feeder forecast
            with cols[0]:
                st.plotly_chart(
                    plot_forecast_data(target_filtered, selected_feeder),
                    use_container_width=True,
                )

            # Pair feeders forecast
            for idx, pair_feeder in enumerate(pair_feeders[:num_pairs]):
                pair_forecast = perform_forecast(pair_feeder, last_date)
                pair_filtered = pair_forecast[
                    (pair_forecast["timestamp"] >= work_start)
                    & (pair_forecast["timestamp"] < work_end)
                ]

                if not pair_filtered.empty:
                    with cols[idx + 1]:
                        st.plotly_chart(
                            plot_forecast_data(pair_filtered, pair_feeder),
                            use_container_width=True,
                        )
        else:
            st.warning("Tidak ada data forecast untuk rentang tanggal yang dipilih")

else:
    st.info("👆 Silakan pilih feeder untuk memulai analisis")
