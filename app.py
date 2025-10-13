import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta, datetime, time
import plotly.graph_objects as go
from pathlib import Path
import base64
from utils.db_util import get_unique_feeders, load_data_from_db
from feeders import birem, gegger, labang, tragah, torjun, galis, unibang

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
# CUSTOM CSS WITH BOOTSTRAP
# ============================================================
st.markdown(f"""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.1.3/dist/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
* {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}}
.stApp {{
    background-color: #e8ecef !important;
}}
.main-header {{
    background-color: #ffffff;
    margin: -50px -80px 0 -80px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    position: sticky;
    z-index: 999;
}}
.logo-section {{
    display: flex;
    align-items: center;
}}
.logo-section img {{
    height: 75px;
    width: auto;
    margin-right: 1rem;
}}
.dashboard-title {{
    font-size: 1.6rem;
    font-weight: 600;
    color: #2c3e50;
    margin: 0;
    letter-spacing: -0.3px;
}}
.filter-container {{
    background: white;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin-bottom: 1rem;
}}
.card {{
    background: white;
    border: none;
    border-radius: 6px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    margin-bottom: 1rem;
    overflow: hidden;
}}
.card-header {{
    background: #1a94aa;
    color: white;
    font-size: 1rem;
    font-weight: 600;
    border: none;
    border-radius: 6px 6px 0 0;
    letter-spacing: -0.2px;
}}
.card-body {{
    padding: 1.2rem;
    border-radius: 0 0 6px 6px;
}}
.rec-card {{
    border-radius: 6px;
    margin-bottom: 0.65rem;
    display: flex;
    align-items: center;
    padding: 0.7rem 1rem;
    transition: all 0.2s ease;
    font-size: 0.9rem;
}}
.rec-card:hover {{
    transform: translateX(4px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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
.rec-content {{
    flex: 1;
}}
.rec-title {{
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 0.15rem;
}}
.rec-subtitle {{
    font-size: 0.8rem;
    opacity: 0.85;
}}
.recommendations-scroll {{
    max-height: 280px;
    overflow-y: auto;
    padding-right: 0.5rem;
}}
.recommendations-scroll::-webkit-scrollbar {{
    width: 6px;
}}
.recommendations-scroll::-webkit-scrollbar-track {{
    background: #f1f1f1;
    border-radius: 10px;
}}
.recommendations-scroll::-webkit-scrollbar-thumb {{
    background: #1a94aa;
    border-radius: 10px;
}}
.data-table {{
    font-size: 0.8rem;
    max-height: 300px;
    overflow-y: auto;
}}
.data-table::-webkit-scrollbar {{
    width: 6px;
}}
.data-table::-webkit-scrollbar-track {{
    background: #f1f1f1;
    border-radius: 10px;
}}
.data-table::-webkit-scrollbar-thumb {{
    background: #1a94aa;
    border-radius: 10px;
}}
.data-table table {{
    width: 100%;
    border-collapse: collapse;
}}
.data-table th {{
    background-color: #f8f9fa;
    color: #2c3e50;
    font-weight: 600;
    padding: 0.65rem 0.75rem;
    text-align: left;
    position: sticky;
    top: 0;
    border-bottom: 2px solid #dee2e6;
    font-size: 0.8rem;
    z-index: 10;
}}
.data-table td {{
    padding: 0.55rem 0.75rem;
    border-bottom: 1px solid #f0f0f0;
}}
.data-table tbody tr:nth-child(even) {{
    background-color: #f9fafb;
}}
.data-table tbody tr:hover {{
    background-color: #f1f5f9;
    transition: background-color 0.15s ease;
}}
.status-badge {{
    display: inline-block;
    padding: 0.25rem 0.65rem;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.3px;
}}
.badge-safe {{
    background-color: #d4edda;
    color: #155724;
}}
.badge-warning {{
    background-color: #fff3cd;
    color: #856404;
}}
.badge-danger {{
    background-color: #f8d7da;
    color: #721c24;
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
    font-weight: 500;
}}
.peak-badge {{
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(255,255,255,0.95);
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    z-index: 10;
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
            "galis": galis,
            "unibang": unibang, 
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

st.markdown('<div class="filter-container">', unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

hour_options = generate_hour_options()

with col1:
    selected_feeder = st.selectbox("Select Feeder", unique_feeders)
with col2:
    start_date = st.date_input("Tanggal Mulai")
with col3:
    start_time = st.selectbox("Jam Mulai", hour_options, index=0, format_func=lambda x: x.strftime("%H:%M"))
with col4:
    end_date = st.date_input("Tanggal Selesai")
with col5:
    end_time = st.selectbox("Jam Selesai", hour_options, index=23, format_func=lambda x: x.strftime("%H:%M"))

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# FORECAST
# ============================================================
partner_results = []

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
        st.error("Tanggal/Jam selesai harus lebih besar dari mulai.")
        st.stop()

    if period_end > (last_data_time + timedelta(hours=FORECAST_HOURS)):
        st.error("Periode melebihi jangkauan forecast (72 jam).")
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
        height=280,
        title=dict(
            text=f"{selected_feeder.upper()}",
            font=dict(size=12, color="#3498db", weight=600),
            x=0.02,
            y=0.98,
            xanchor='left',
            yanchor='top'
        ),
        template="plotly_white",
        margin=dict(l=0, r=0, t=35, b=0),
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
    
    html_parts = []
    html_parts.append('<div class="card">')
    html_parts.append('<div class="card-header">Rekomendasi Manuver</div>')
    html_parts.append('<div class="card-body">')
    html_parts.append('<div class="recommendations-scroll">')
    
    if not partner_list:
        html_parts.append('<p class="text-muted">Feeder ini tidak memiliki pasangan transfer.</p>')
    else:
        partner_results = []
        
        for partner in partner_list:
            try:
                df_partner = load_data_from_db(partner)
                if df_partner.empty:
                    continue
                
                # Konversi tipe data
                df_partner["arus"] = pd.to_numeric(df_partner["arus"], errors="coerce")
                df_partner.dropna(subset=["arus"], inplace=True)
                df_partner["timestamp"] = pd.to_datetime(df_partner["timestamp"])
                
                fc_partner = call_forecast_module(partner, df_partner, period_start)
                if fc_partner is None or fc_partner.empty:
                    continue

                # Normalisasi kolom
                if "datetime" in fc_partner.columns:
                    fc_partner = fc_partner.rename(columns={"datetime": "timestamp"})
                fc_partner["timestamp"] = pd.to_datetime(fc_partner["timestamp"])
                
                # Resample to hourly
                fc_partner_hourly = resample_to_hourly(fc_partner, 'timestamp', 'forecast')
                if fc_partner_hourly is None or fc_partner_hourly.empty:
                    continue
                
                # Filter based on user input
                fc_partner_filtered = fc_partner_hourly[
                    (fc_partner_hourly["timestamp"] >= period_start) & 
                    (fc_partner_hourly["timestamp"] <= period_end)
                ].copy()
                
                if fc_partner_filtered.empty:
                    continue

                # Merge dengan forecast utama
                merged = pd.merge(
                    fc_filtered,
                    fc_partner_filtered,
                    on="timestamp",
                    suffixes=("_main", "_partner")
                )
                
                if merged.empty:
                    continue

                # Hitung total transfer
                merged["total_transfer"] = merged["forecast_main"] + merged["forecast_partner"]
                max_load = round(merged["total_transfer"].max(), 2)

                # Tentukan status
                if max_load < 320:
                    status = "safe"
                    label = "Aman"
                elif 320 <= max_load < 400:
                    status = "warning"
                    label = "Mendekati Batas"
                else:
                    status = "danger"
                    label = "Tidak Aman"

                # Simpan hasil
                partner_results.append((partner, max_load, status, label, fc_partner_filtered))

                # Build card HTML
                card_html = '<div class="rec-card ' + status + '">'
                card_html += '<div class="rec-content">'
                card_html += '<div class="rec-title">' + partner.upper() + '</div>'
                card_html += '<div class="rec-subtitle">' + label + ' (Maks: ' + str(max_load) + ' A)</div>'
                card_html += '</div>'
                card_html += '</div>'
                
                html_parts.append(card_html)
                
            except Exception as e:
                continue
        
        if not partner_results:
            html_parts.append('<p class="text-muted">Tidak ada rekomendasi yang tersedia untuk periode ini.</p>')

    html_parts.append('</div>')   
    html_parts.append('</div>')   
    html_parts.append('</div>')  
    
    final_html = ''.join(html_parts)
    st.markdown(final_html, unsafe_allow_html=True)

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
            marker=dict(size=5, color="#2ecc71"),
            fill='tozeroy',
            fillcolor='rgba(46,204,113,0.15)'
        ))
        fig_fc.add_hline(
            y=320,
            line=dict(color="#e74c3c", dash="dash", width=2),
            annotation_text="Batas Aman (320 A)",
            annotation_position="top right"
        )
        fig_fc.update_layout(
            height=300,
            title=dict(
                text=f"{selected_feeder.upper()}",
                font=dict(size=12, color="#2ecc71", weight=600),
                x=0.02,
                y=0.98,
                xanchor='left',
                yanchor='top'
            ),
            template="plotly_white",
            margin=dict(l=0, r=0, t=35, b=0),
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
        table_html = (
            '<div class="card">'
            '<div class="card-header">Rincian Prediksi Per Jam</div>'
            '<div class="card-body"><div class="data-table"><table>'
            '<thead><tr><th>Waktu</th><th>Arus (A)</th></tr></thead><tbody>'
        )

        for _, row in fc_filtered.iterrows():
            dt = row["timestamp"]
            forecast_val = round(row["forecast"], 2)
            time_str = dt.strftime("%d %b %H:%M")
            table_html += f'<tr><td>{time_str}</td><td>{forecast_val}</td></tr>'

        table_html += '</tbody></table></div></div></div>'
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="card"><div class="card-header">Rincian Prediksi Per Jam</div>'
            '<div class="card-body"><p class="text-muted">Tidak ada data untuk ditampilkan</p></div></div>',
            unsafe_allow_html=True
        )

# ========================================================
# ROW 3: DETAIL PREDIKSI FEEDER PASANGAN
# ========================================================
if partner_results:
    st.markdown('<div class="card"><div class="card-header">Prediksi Feeder Manuver</div></div>', unsafe_allow_html=True)
    
    cols = st.columns(3)
    for idx, (partner, max_load, status, label, df_fc) in enumerate(partner_results):
        with cols[idx % 3]:
            color = "#28a745" if status == "safe" else "#ffc107" if status == "warning" else "#dc3545"
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_fc["timestamp"],
                y=df_fc["forecast"].round(2),
                mode="lines+markers",
                line=dict(color=color, width=2.5),
                marker=dict(size=4, color=color),
                fill='tozeroy',
                fillcolor='rgba(0,0,0,0.05)'
            ))
            fig.update_layout(
                height=220,
                title=dict(text=f"{partner.upper()}", font=dict(size=12, color=color, weight=600)),
                template="plotly_white",
                margin=dict(l=0, r=0, t=35, b=0),
                xaxis_title="Waktu",
                yaxis_title="Arus (A)",
                xaxis=dict(showgrid=True, gridcolor='#f0f0f0', tickformat="%d %b\n%H:%M", tickfont=dict(size=9)),
                yaxis=dict(showgrid=True, gridcolor='#f0f0f0', tickfont=dict(size=9)),
                plot_bgcolor='white',
                paper_bgcolor='white',
                annotations=[
                    dict(
                        text=f"Peak: {max_load} A",
                        xref="paper", yref="paper",
                        x=0.98, y=0.98,
                        xanchor="right", yanchor="top",
                        showarrow=False,
                        bgcolor="rgba(255,255,255,0.95)",
                        bordercolor=color,
                        borderwidth=1,
                        borderpad=4,
                        font=dict(size=9, color=color, weight=600)
                    )
                ]
            )
            st.plotly_chart(fig, use_container_width=True)
