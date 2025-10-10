import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta, datetime, time
import plotly.graph_objects as go
from pathlib import Path
import base64
from utils.db_util import get_unique_feeders, load_data_from_db
from feeders import birem, gegger, labang, tragah, torjun

# ============================================================
# PAGE CONFIG & LOGO
# ============================================================
st.set_page_config(page_title="Load Monitor & Forecast System", layout="wide")

logo_path = Path(r"D:\Magang\ForecastArus\loadstar.png")

def get_base64_logo(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = get_base64_logo(logo_path) if logo_path.exists() else ""

# ============================================================
# CUSTOM CSS WITH BOOTSTRAP - HEADER & BACKGROUND ONLY
# ============================================================
st.markdown(f"""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.1.3/dist/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">
<style>
.stApp {{
    background-color: #e8ecef !important;
}}
.main-header {{
    background-color: #ffffff;
    padding: 1.2rem 2.5rem;
    margin: -50px -80px 2rem -80px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    position: sticky;
    z-index: 999;
}}
.logo-section {{
    display: flex;
    align-items: center;
}}
.logo-section img {{
    height: 90px;
    width: auto;
    margin-right: 1.2rem;
}}
.dashboard-title {{
    font-size: 1.75rem;
    font-weight: 600;
    color: #2c3e50;
    margin: 0;
}}
.card {{
    background: white;
    border: none;
    border-radius: 0px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    margin-bottom: 1.5rem;
    overflow: hidden;
}}
.card-header {{
    background: #1a94aa;
    color: white;
    font-size: 1.1rem;
    font-weight: 600;
    padding: 1rem 1.5rem;
    border: none;
    border-radius: 0px; 
}}
.card-body {{
    padding: 1.5rem;
    border-radius: 0px; 
}}
.rec-card {{
    border-radius: 0px; 
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    transition: transform 0.2s;
}}
.rec-card:hover {{
    transform: translateX(5px);
}}
.rec-card.safe {{
    background-color: #d4edda;
    color: #155724;
    border-left: 4px solid #28a745;
}}
.rec-card.warning {{
    background-color: #fff3cd;
    color: #856404;
    border-left: 4px solid #ffc107;
}}
.rec-card.danger {{
    background-color: #f8d7da;
    color: #721c24;
    border-left: 4px solid #dc3545;
}}
.rec-icon {{
    font-size: 1.5rem;
    min-width: 30px;
    text-align: center;
    margin-right: 1rem;
}}
.data-table {{
    font-size: 0.85rem;
    max-height: 320px;
    overflow-y: auto;
}}
.data-table table {{
    width: 100%;
    border-collapse: collapse;
}}
.data-table th {{
    background-color: #f8f9fa;
    color: #2c3e50;
    font-weight: 600;
    padding: 0.6rem;
    text-align: left;
    position: sticky;
    top: 0;
    border-bottom: 2px solid #dee2e6;
}}
.data-table td {{
    padding: 0.5rem 0.6rem;
    border-bottom: 1px solid #f0f0f0;
}}
.data-table tr:hover {{
    background-color: #f8f9fa;
}}
.high-load {{
    color: #dc3545;
    font-weight: 600;
}}
.medium-load {{
    color: #ffc107;
    font-weight: 600;
}}
.low-load {{
    color: #28a745;
}}
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
.stPlotlyChart {{
    background: white;
}}
</style>

<div class="main-header">
    <div class="logo-section">
        <img src="data:image/png;base64,{logo_base64}" alt="LoadStar Logo">
        <div class="dashboard-title">Load Forecaster Dashboard</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# KONSTANTA
# ============================================================
FORECAST_HOURS = 72
MAX_CAPACITY = 400.0
WARNING_THRESHOLD = 320.0
HIST_DAYS = 7

# ============================================================
# RELASI FEEDER
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
for asal, tujuan_list in list(feeder_pairs.items()):
    for tujuan in tujuan_list:
        feeder_pairs.setdefault(tujuan.lower(), [])
        if asal.lower() not in feeder_pairs[tujuan.lower()]:
            feeder_pairs[tujuan.lower()].append(asal.lower())
feeder_pairs = {k.lower(): [t.lower() for t in v] for k, v in feeder_pairs.items()}

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def normalize_forecast_df(fc):
    if fc is None:
        return None
    df = fc.copy()
    if "datetime" not in df.columns:
        for alt in ["timestamp", "ds", "date"]:
            if alt in df.columns:
                df = df.rename(columns={alt: "datetime"})
                break
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    if "forecast" not in df.columns:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if num_cols:
            df = df.rename(columns={num_cols[0]: "forecast"})
        else:
            return None
    return df.dropna().sort_values("datetime").reset_index(drop=True)

def call_forecast_module(name, historical_df, start_datetime):
    if historical_df is None or historical_df.empty:
        return None
    name = name.lower()
    try:
        module_map = {
            "birem": birem,
            "gegger": gegger,
            "labang": labang,
            "tragah": tragah,
            "torjun": torjun,
        }
        module = module_map.get(name)
        if not module:
            return None
        raw_fc = module.forecast(historical_df.set_index("timestamp"), steps=FORECAST_HOURS, start_datetime=start_datetime)
    except Exception as e:
        st.error(f"Error model '{name}': {e}")
        return None
    return normalize_forecast_df(raw_fc)

def resample_to_hourly(df, datetime_col='datetime', value_col='forecast'):
    """Resample data to hourly frequency"""
    if df is None or df.empty:
        return None
    df = df.copy()
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df = df.set_index(datetime_col)
    df_hourly = df[value_col].resample('H').mean().reset_index()
    df_hourly.columns = [datetime_col, value_col]
    return df_hourly

def generate_hour_options():
    """Generate hourly time options from 00:00 to 23:00"""
    return [time(h, 0) for h in range(24)]

# ============================================================
# INPUT
# ============================================================
unique_feeders = get_unique_feeders()
if not unique_feeders:
    st.error("Tidak ada feeder ditemukan di database.")
    st.stop()

col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

hour_options = generate_hour_options()

with col1:
    selected_feeder = st.selectbox("Select Feeder", unique_feeders)
with col2:
    start_date = st.date_input("Tanggal Mulai Pekerjaan")
with col3:
    start_time = st.selectbox("Jam Mulai", hour_options, index=0, format_func=lambda x: x.strftime("%H:%M"))
with col4:
    end_date = st.date_input("Tanggal Selesai Pekerjaan")
with col5:
    end_time = st.selectbox("Jam Selesai", hour_options, index=23, format_func=lambda x: x.strftime("%H:%M"))

# ============================================================
# FORECAST
# ============================================================
if selected_feeder and start_date and end_date:
    df_hist = load_data_from_db(selected_feeder)
    if df_hist.empty:
        st.error("Data historis tidak ditemukan.")
        st.stop()

    df_hist["arus"] = pd.to_numeric(df_hist["arus"], errors="coerce")
    df_hist.dropna(subset=["arus"], inplace=True)
    df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])
    last_data_time = df_hist["timestamp"].max()

    period_start = pd.to_datetime(datetime.combine(start_date, start_time))
    period_end = pd.to_datetime(datetime.combine(end_date, end_time))

    if period_end <= period_start:
        st.error("❌ Tanggal/Jam selesai harus lebih besar dari mulai.")
        st.stop()

    if period_end > (last_data_time + timedelta(hours=FORECAST_HOURS)):
        st.error("❌ Periode melebihi jangkauan forecast (72 jam).")
        st.stop()

    df_hist_display = df_hist[df_hist["timestamp"] >= (last_data_time - timedelta(days=HIST_DAYS))].copy()
    fc_main = call_forecast_module(selected_feeder, df_hist, period_start)
    if fc_main is None or fc_main.empty:
        st.warning(f"Feeder '{selected_feeder}' belum memiliki model forecast.")
        st.stop()

    # Normalize column names
    if "datetime" in fc_main.columns:
        fc_main = fc_main.rename(columns={"datetime": "timestamp"})
    fc_main["timestamp"] = pd.to_datetime(fc_main["timestamp"])

    # Resample to hourly
    fc_main_hourly = resample_to_hourly(fc_main, 'timestamp', 'forecast')
    
    # Filter based on user input
    fc_filtered = fc_main_hourly[
        (fc_main_hourly["timestamp"] >= period_start) & 
        (fc_main_hourly["timestamp"] <= period_end)
    ].copy()

    # ========================================================
    # ROW 1: BEBAN REAL-TIME & REKOMENDASI MANUVER
    # ========================================================
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown('<div class="card"><div class="card-header">Beban Real-Time</div></div>', unsafe_allow_html=True)
        
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Scatter(
            x=df_hist_display["timestamp"],
            y=df_hist_display["arus"].round(2),
            mode="lines",
            line=dict(color="#3498db", width=2.5),
            fill='tozeroy',
            fillcolor='rgba(52,152,219,0.15)'
        ))
        fig_hist.update_layout(
            height=320,
            template="plotly_white",
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title="Waktu",
            yaxis_title="Arus (A)",
            xaxis=dict(showgrid=True, gridcolor='#f0f0f0', tickformat="%d %b\n%H:%M"),
            yaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_right:
        partner_list = feeder_pairs.get(selected_feeder.lower(), [])
        
        recommendations_html = '<div class="card"><div class="card-header">Rekomendasi Manuver</div><div class="card-body">'
        
        if not partner_list:
            recommendations_html += '<p class="text-muted">Feeder ini tidak memiliki pasangan transfer.</p>'
        else:
            partner_results = []

            for partner in partner_list:
                df_partner = load_data_from_db(partner)
                if df_partner.empty:
                    continue
                fc_partner = call_forecast_module(partner, df_partner, period_start)
                if fc_partner is None or fc_partner.empty:
                    continue

                if "datetime" in fc_partner.columns:
                    fc_partner = fc_partner.rename(columns={"datetime": "timestamp"})
                fc_partner["timestamp"] = pd.to_datetime(fc_partner["timestamp"])
                
                # Resample to hourly
                fc_partner_hourly = resample_to_hourly(fc_partner, 'timestamp', 'forecast')
                
                # Filter based on user input
                fc_partner_filtered = fc_partner_hourly[
                    (fc_partner_hourly["timestamp"] >= period_start) & 
                    (fc_partner_hourly["timestamp"] <= period_end)
                ]

                merged = pd.merge(fc_filtered, fc_partner_filtered, on="timestamp", suffixes=(f"_{selected_feeder}", f"_{partner}"))
                if merged.empty:
                    continue

                merged["total_transfer"] = merged[f"forecast_{selected_feeder}"] + merged[f"forecast_{partner}"]
                max_load = round(merged["total_transfer"].max(), 2)

                if max_load < 320:
                    status, icon, label = "safe", "✓", "Aman"
                elif 320 <= max_load < 400:
                    status, icon, label = "warning", "⚠", "Mendekati Batas"
                else:
                    status, icon, label = "danger", "⨂", "Tidak Aman"

                partner_results.append((partner, max_load, status, icon, label, fc_partner_filtered))

            partner_results = sorted(partner_results, key=lambda x: x[1])
            for partner, max_load, status, icon, label, _ in partner_results:
                recommendations_html += f"""
                <div class="rec-card {status}">
                    <div class="rec-icon">{icon}</div>
                    <div>
                        <strong>{partner.upper()}</strong><br>
                        <small>{label} (Maks: {max_load} A)</small>
                    </div>
                </div>
                """
        
        recommendations_html += '</div></div>'
        st.markdown(recommendations_html, unsafe_allow_html=True)

    # ========================================================
    # ROW 2: PREDIKSI 72 JAM + TABEL RINCIAN
    # ========================================================
    col_chart, col_table = st.columns([2, 1])
    
    with col_chart:
        st.markdown('<div class="card"><div class="card-header">Prediksi Beban 72 Jam ke Depan</div></div>', unsafe_allow_html=True)
        
        if not fc_filtered.empty:
            fig_fc = go.Figure()
            fig_fc.add_trace(go.Scatter(
                x=fc_filtered["timestamp"],
                y=fc_filtered["forecast"].round(2),
                mode="lines+markers",
                line=dict(color="#2ecc71", width=3),
                marker=dict(size=6, color="#2ecc71"),
                fill='tozeroy',
                fillcolor='rgba(46,204,113,0.15)'
            ))
            fig_fc.add_hline(y=WARNING_THRESHOLD, line=dict(color="#e74c3c", dash="dash", width=2),
                             annotation_text="Batas Aman (320 A)", annotation_position="top right")
            fig_fc.update_layout(
                height=350,
                template="plotly_white",
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis_title="Waktu",
                yaxis_title="Arus (A)",
                xaxis=dict(showgrid=True, gridcolor='#f0f0f0', tickformat="%d %b\n%H:%M"),
                yaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig_fc, use_container_width=True)
        else:
            st.warning("Tidak ada data forecast dalam rentang tanggal yang dipilih.")

    with col_table:
        if not fc_filtered.empty:
            table_html = '<div class="card"><div class="card-header">Rincian Prediksi Per Jam</div><div class="card-body"><div class="data-table"><table>'
            table_html += '<thead><tr><th>Waktu</th><th>Arus (A)</th><th>Status</th></tr></thead><tbody>'
            
            for _, row in fc_filtered.iterrows():
                dt = row["timestamp"]
                forecast_val = round(row["forecast"], 2)
                
                if forecast_val >= 400:
                    status_class = "high-load"
                    status_text = "⚠ Bahaya"
                elif forecast_val >= 320:
                    status_class = "medium-load"
                    status_text = "⚡ Tinggi"
                else:
                    status_class = "low-load"
                    status_text = "✓ Normal"
                
                time_str = dt.strftime("%d %b %H:%M")
                table_html += f'<tr><td>{time_str}</td><td class="{status_class}">{forecast_val}</td><td><small>{status_text}</small></td></tr>'
            
            table_html += '</tbody></table></div></div></div>'
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="card"><div class="card-header">Rincian Prediksi Per Jam</div><div class="card-body"><p class="text-muted">Tidak ada data untuk ditampilkan</p></div></div>', unsafe_allow_html=True)
            
    # ========================================================
    # ROW 3: DETAIL PREDIKSI FEEDER PASANGAN
    # ========================================================
    if partner_results:
        st.markdown('<div class="card"><div class="card-header">Prediksi Feeder Manuver</div></div>', unsafe_allow_html=True)
        
        cols = st.columns(2)
        for idx, (partner, max_load, status, icon, label, df_fc) in enumerate(partner_results):
            with cols[idx % 2]:
                color = "#28a745" if status == "safe" else "#ffc107" if status == "warning" else "#dc3545"
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_fc["timestamp"],
                    y=df_fc["forecast"].round(2),
                    mode="lines+markers",
                    line=dict(color=color, width=2.5),
                    marker=dict(size=5, color=color),
                    fill='tozeroy',
                    fillcolor=f'rgba(0,0,0,0.05)'
                ))
                fig.update_layout(
                    height=240,
                    title=dict(text=f"{partner.upper()} — {label}", font=dict(size=13, color=color)),
                    template="plotly_white",
                    margin=dict(l=0, r=0, t=40, b=0),
                    xaxis_title="Waktu",
                    yaxis_title="Arus (A)",
                    xaxis=dict(showgrid=True, gridcolor='#f0f0f0', tickformat="%d %b\n%H:%M"),
                    yaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                st.plotly_chart(fig, use_container_width=True)