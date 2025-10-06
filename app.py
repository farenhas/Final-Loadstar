import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go
from utils.db_util import get_unique_feeders, get_historical_data

# ======================================================
# ⚙️ BASIC CONFIGURATION
# ======================================================
st.set_page_config(page_title="Load Monitor System", layout="wide", page_icon="⚡")

# ======================================================
# 🎨 CUSTOM CSS - ENHANCED DESIGN
# ======================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 25%, #0f1829 50%, #1e2a4a 75%, #0a0e27 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main-header {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(59, 130, 246, 0.15) 50%, rgba(139, 92, 246, 0.15) 100%);
        border: 2px solid rgba(6, 182, 212, 0.4);
        border-radius: 24px;
        padding: 40px 30px;
        margin-bottom: 35px;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(6, 182, 212, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(6, 182, 212, 0.1) 0%, transparent 70%);
        animation: rotate 20s linear infinite;
    }
    
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .main-title {
        font-size: 3.2em;
        font-weight: 900;
        background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 50%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        text-align: center;
        letter-spacing: -2px;
        position: relative;
        z-index: 1;
        text-shadow: 0 0 40px rgba(6, 182, 212, 0.3);
    }
    
    .subtitle {
        color: #cbd5e1;
        text-align: center;
        font-size: 1.15em;
        margin-top: 12px;
        font-weight: 500;
        letter-spacing: 0.5px;
        position: relative;
        z-index: 1;
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 12px;
        color: #10b981;
        font-size: 0.75em;
        font-weight: 600;
        margin-left: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .control-panel {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 100%);
        border: 2px solid rgba(6, 182, 212, 0.3);
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 30px;
        backdrop-filter: blur(15px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    
    .control-title {
        color: #06b6d4;
        font-size: 1.3em;
        font-weight: 700;
        margin-bottom: 20px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        text-align: center;
    }
    
    .section-header {
        color: #cbd5e1;
        font-size: 1.8em;
        font-weight: 800;
        margin: 35px 0 20px 0;
        padding-left: 15px;
        border-left: 4px solid #06b6d4;
        letter-spacing: 0.5px;
    }
    
    .chart-container {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.85) 100%);
        border: 2px solid rgba(6, 182, 212, 0.25);
        border-radius: 20px;
        padding: 25px;
        margin: 18px 0;
        backdrop-filter: blur(15px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.3s ease;
    }
    
    .chart-container:hover {
        border-color: rgba(6, 182, 212, 0.4);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 100%);
        border: 2px solid rgba(6, 182, 212, 0.3);
        border-radius: 20px;
        padding: 28px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        height: 100%;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.1), transparent);
        transition: left 0.5s;
    }
    
    .metric-card:hover::before {
        left: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 16px 48px rgba(6, 182, 212, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border-color: rgba(6, 182, 212, 0.6);
    }
    
    .metric-icon {
        font-size: 2.5em;
        margin-bottom: 10px;
        opacity: 0.8;
    }
    
    .metric-label {
        color: #06b6d4;
        font-size: 0.85em;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 12px;
        opacity: 0.9;
    }
    
    .metric-value {
        color: white;
        font-size: 2.8em;
        font-weight: 900;
        line-height: 1;
        margin: 15px 0;
        font-family: 'JetBrains Mono', monospace;
        text-shadow: 0 2px 10px rgba(6, 182, 212, 0.3);
    }
    
    .metric-status {
        color: #10b981;
        font-size: 0.9em;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    .status-operational {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.15) 100%);
        border: 3px solid rgba(16, 185, 129, 0.5);
    }
    
    .status-operational::after {
        content: '';
        position: absolute;
        top: 20px;
        right: 20px;
        width: 12px;
        height: 12px;
        background: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.8);
        animation: pulse-dot 2s ease-in-out infinite;
    }
    
    @keyframes pulse-dot {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.3); opacity: 0.7; }
    }
    
    .status-value {
        color: #10b981;
        font-size: 3em;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 30px rgba(16, 185, 129, 0.5);
    }
    
    .status-warning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(217, 119, 6, 0.15) 100%);
        border: 3px solid rgba(245, 158, 11, 0.5);
    }
    
    .warning-value {
        color: #f59e0b;
        text-shadow: 0 0 30px rgba(245, 158, 11, 0.5);
    }
    
    .status-reject {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.15) 100%);
        border: 3px solid rgba(239, 68, 68, 0.5);
    }
    
    .reject-value {
        color: #ef4444;
        text-shadow: 0 0 30px rgba(239, 68, 68, 0.5);
    }
    
    .stSelectbox > div > div {
        background: rgba(15, 23, 42, 0.95);
        border: 2px solid rgba(6, 182, 212, 0.3);
        border-radius: 12px;
        color: white;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:hover {
        border-color: rgba(6, 182, 212, 0.5);
        box-shadow: 0 4px 12px rgba(6, 182, 212, 0.2);
    }
    
    .stDateInput > div > div > input {
        background: rgba(15, 23, 42, 0.95);
        border: 2px solid rgba(6, 182, 212, 0.3);
        border-radius: 12px;
        color: white;
        transition: all 0.3s ease;
    }
    
    .stDateInput > div > div > input:hover {
        border-color: rgba(6, 182, 212, 0.5);
    }
    
    .stCheckbox {
        background: rgba(15, 23, 42, 0.5);
        border-radius: 8px;
        padding: 10px;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 14px 32px;
        font-weight: 700;
        font-size: 1.05em;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(6, 182, 212, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(6, 182, 212, 0.5);
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    }
    
    .custom-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.5), transparent);
        margin: 30px 0;
    }
    
    /* CUSTOM TABLE STYLING */
    div[data-testid="stDataFrame"] {
        background: transparent !important;
    }
    
    div[data-testid="stDataFrame"] > div {
        background: rgba(15, 23, 42, 0.6) !important;
        border-radius: 16px !important;
        border: 2px solid rgba(6, 182, 212, 0.3) !important;
        overflow: hidden !important;
    }
    
    div[data-testid="stDataFrame"] table {
        border-collapse: separate !important;
        border-spacing: 0 !important;
    }
    
    div[data-testid="stDataFrame"] thead tr th {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.25) 0%, rgba(59, 130, 246, 0.25) 100%) !important;
        color: #06b6d4 !important;
        font-weight: 700 !important;
        font-size: 0.85em !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        padding: 16px 12px !important;
        border-bottom: 2px solid rgba(6, 182, 212, 0.4) !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 10 !important;
    }
    
    div[data-testid="stDataFrame"] tbody tr {
        background: rgba(15, 23, 42, 0.4) !important;
        transition: all 0.2s ease !important;
    }
    
    div[data-testid="stDataFrame"] tbody tr:hover {
        background: rgba(6, 182, 212, 0.15) !important;
        transform: scale(1.01) !important;
        box-shadow: 0 4px 12px rgba(6, 182, 212, 0.2) !important;
    }
    
    div[data-testid="stDataFrame"] tbody tr td {
        color: #e2e8f0 !important;
        padding: 14px 12px !important;
        border-bottom: 1px solid rgba(100, 116, 139, 0.2) !important;
        font-size: 0.95em !important;
    }
    
    div[data-testid="stDataFrame"] tbody tr:nth-child(even) {
        background: rgba(30, 41, 59, 0.3) !important;
    }
    
    /* Row index styling */
    div[data-testid="stDataFrame"] tbody tr td:first-child {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    [data-testid="column"] {
        padding: 0 8px;
    }
</style>
""", unsafe_allow_html=True)

# ======================================================
# 📊 HEADER
# ======================================================
st.markdown("""
<div class="main-header">
    <h1 class="main-title">CURRENT MONITORING SYSTEM</h1>
    <p class="subtitle">Current Forecasting & Transfer Analysis Between Feeders<span class="status-badge">ONLINE</span></p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# 🎛️ CONTROL PANEL
# ======================================================
st.markdown('<div class="control-panel">', unsafe_allow_html=True)
st.markdown('<div class="control-title">Analysis Configuration</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

with col1:
    feeders = sorted(get_unique_feeders())
    selected_feeder = st.selectbox("Primary Feeder", feeders, key="main_feeder")

with col2:
    start_date = st.date_input("From Date", datetime.now() - timedelta(days=7))

with col3:
    end_date = st.date_input("To Date", datetime.now())

with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    simulate_overload = st.checkbox("Simulate Overload", value=False)

st.markdown('</div>', unsafe_allow_html=True)

dummy_boost = 250 if simulate_overload else 0
CAPACITY = 400

# ======================================================
# 📊 LOAD HISTORICAL DATA
# ======================================================
@st.cache_data
def load_data(feeder, start, end):
    df = get_historical_data(feeder, start, end)
    if df.empty:
        return df
    df['jam_order'] = df['jam'].apply(lambda x: int(x.split('_')[0]) * 60)
    df = df.sort_values(by=['tanggal', 'jam_order']).drop(columns=['jam_order'])
    return df

data = load_data(selected_feeder, start_date, end_date)

st.markdown('<div class="section-header">Historical Data Overview</div>', unsafe_allow_html=True)

if data.empty:
    st.warning("No historical data available for this feeder in the selected date range.")
    st.stop()

st.success(f"Displaying data for feeder **{selected_feeder}** from **{start_date}** to **{end_date}**")
st.dataframe(data[['datetime', 'arus']], use_container_width=True, height=280)

# HISTORICAL CHART with enhanced styling
st.markdown('<div class="chart-container">', unsafe_allow_html=True)
fig_hist = go.Figure()

# Area fill with gradient
fig_hist.add_trace(go.Scatter(
    x=data['datetime'], 
    y=data['arus'], 
    mode='lines', 
    name='Historical Current',
    line=dict(color='#06b6d4', width=0),
    fill='tozeroy',
    fillcolor='rgba(6, 182, 212, 0.3)',
    hovertemplate='<b>%{x}</b><br>Current: %{y:.2f} A<extra></extra>'
))

# Main line
fig_hist.add_trace(go.Scatter(
    x=data['datetime'], 
    y=data['arus'], 
    mode='lines+markers', 
    name='Historical Current',
    line=dict(color='#06b6d4', width=3.5, shape='spline'),
    marker=dict(
        size=7, 
        color='#06b6d4',
        line=dict(color='#ffffff', width=2),
        symbol='circle'
    ),
    showlegend=False,
    hovertemplate='<b>%{x}</b><br>Current: %{y:.2f} A<extra></extra>'
))

# Peak marker
max_idx = data['arus'].idxmax()
fig_hist.add_trace(go.Scatter(
    x=[data.loc[max_idx, 'datetime']], 
    y=[data.loc[max_idx, 'arus']],
    mode='markers+text',
    name='Peak Load',
    marker=dict(size=15, color='#ef4444', line=dict(color='white', width=3)),
    text=[f"Peak: {data.loc[max_idx, 'arus']:.1f}A"],
    textposition="top center",
    textfont=dict(color='#ef4444', size=12, family='JetBrains Mono'),
    showlegend=False
))

fig_hist.update_layout(
    title=dict(
        text=f"<b>Historical Current - Feeder {selected_feeder}</b>",
        font=dict(size=20, color='#cbd5e1', family='Inter')
    ),
    xaxis=dict(
        title='Datetime',
        gridcolor='rgba(148, 163, 184, 0.1)',
        showgrid=True,
        zeroline=False,
        linecolor='rgba(148, 163, 184, 0.3)'
    ),
    yaxis=dict(
        title='Current (A)',
        gridcolor='rgba(148, 163, 184, 0.1)',
        showgrid=True,
        zeroline=False,
        linecolor='rgba(148, 163, 184, 0.3)'
    ),
    template="plotly_dark",
    plot_bgcolor='rgba(15, 23, 42, 0.2)',
    paper_bgcolor='rgba(0, 0, 0, 0)',
    height=450,
    font=dict(color='#cbd5e1', family='Inter'),
    hovermode='x unified',
    margin=dict(l=60, r=40, t=80, b=60)
)

st.plotly_chart(fig_hist, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ======================================================
# 🔮 STEP 1: PRIMARY FEEDER FORECAST
# ======================================================
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-header">Step 1: Primary Feeder Forecast</div>', unsafe_allow_html=True)
forecast_btn = st.button("Run Primary Feeder Forecast")

if forecast_btn:
    with st.spinner("Running forecast analysis..."):
        try:
            feeder_module = __import__(f"feeders.{selected_feeder.lower()}", fromlist=['forecast'])
        except ModuleNotFoundError:
            st.error(f"Model for feeder {selected_feeder} is not available yet.")
            st.stop()
        
        df_hist = data[['datetime', 'arus']].set_index('datetime')
        forecast_start = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        forecast_df = feeder_module.forecast(df_hist, steps=72, start_datetime=forecast_start)
        forecast_df['forecast'] = forecast_df['forecast'].round(2)
        if simulate_overload:
            forecast_df['forecast'] += dummy_boost
            st.warning(f"Overload simulation active — adding {dummy_boost}A to all forecast points.")
        
        st.session_state["main_forecast"] = {"feeder": selected_feeder, "data": forecast_df}
        
        st.success(f"Forecast completed for feeder {selected_feeder}")
        st.dataframe(forecast_df, use_container_width=True, height=280)

        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        fig_main = go.Figure()
        
        # Historical with area fill
        fig_main.add_trace(go.Scatter(
            x=df_hist.index, 
            y=df_hist['arus'], 
            name="Historical", 
            mode="lines",
            line=dict(color='#3b82f6', width=3, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.2)'
        ))
        
        # Forecast with area fill
        fig_main.add_trace(go.Scatter(
            x=forecast_df['datetime'], 
            y=forecast_df['forecast'], 
            name="72-Hour Forecast", 
            mode="lines+markers", 
            line=dict(color="#f59e0b", width=3.5, dash="dot", shape='spline'),
            marker=dict(size=6, color='#f59e0b', line=dict(color='white', width=1.5)),
            fill='tozeroy',
            fillcolor='rgba(245, 158, 11, 0.15)'
        ))
        
        # Capacity line
        fig_main.add_hline(
            y=CAPACITY, 
            line_dash="dash", 
            line_color="#ef4444", 
            line_width=3,
            annotation_text=f"Maximum Capacity: {CAPACITY}A",
            annotation_position="right",
            annotation=dict(font=dict(size=12, color='#ef4444', family='JetBrains Mono'))
        )
        
        # Warning zone
        fig_main.add_hrect(
            y0=CAPACITY*0.9, y1=CAPACITY,
            fillcolor="rgba(245, 158, 11, 0.1)",
            line_width=0,
            annotation_text="Warning Zone",
            annotation_position="right"
        )
        
        fig_main.update_layout(
            title=dict(
                text=f"<b>Forecast vs Historical - Feeder {selected_feeder}</b>",
                font=dict(size=20, color='#cbd5e1', family='Inter')
            ),
            template="plotly_dark",
            plot_bgcolor='rgba(15, 23, 42, 0.2)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            height=450,
            font=dict(color='#cbd5e1', family='Inter'),
            hovermode='x unified',
            xaxis=dict(
                gridcolor='rgba(148, 163, 184, 0.1)',
                showgrid=True,
                title='Datetime'
            ),
            yaxis=dict(
                gridcolor='rgba(148, 163, 184, 0.1)',
                showgrid=True,
                title='Current (A)'
            ),
            margin=dict(l=60, r=40, t=80, b=60)
        )
        st.plotly_chart(fig_main, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ======================================================
# 🔗 STEP 2: LOAD TRANSFER ANALYSIS & RECOMMENDATIONS
# ======================================================
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-header">Step 2: Load Transfer Analysis & Recommendations</div>', unsafe_allow_html=True)

if "main_forecast" not in st.session_state:
    st.info("Please run the primary feeder forecast first.")
    st.stop()

main_feeder = st.session_state["main_forecast"]["feeder"]
main_forecast = st.session_state["main_forecast"]["data"]

# FEEDER PAIR DEFINITIONS
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

# Create bidirectional connections automatically
for asal, tujuan_list in list(feeder_pairs.items()):
    for tujuan in tujuan_list:
        feeder_pairs.setdefault(tujuan.lower(), [])
        if asal.lower() not in feeder_pairs[tujuan.lower()]:
            feeder_pairs[tujuan.lower()].append(asal.lower())

possible_pairs = feeder_pairs.get(main_feeder.lower(), [])
if not possible_pairs:
    st.warning("This feeder has no available transfer pairs.")
    st.stop()

# Forecast all paired feeders
st.markdown("### Forecast for All Paired Feeders")
pair_forecasts = {}
for pair in possible_pairs:
    try:
        pair_module = __import__(f"feeders.{pair.lower()}", fromlist=['forecast'])
    except ModuleNotFoundError:
        st.warning(f"Model for feeder {pair} is not available. Skipping.")
        continue
    df_pair_hist = load_data(pair, start_date, end_date)
    if df_pair_hist.empty:
        st.warning(f"No historical data available for feeder {pair}. Skipping.")
        continue
    df_pair_hist = df_pair_hist[['datetime', 'arus']].set_index('datetime')
    forecast_pair = pair_module.forecast(df_pair_hist, steps=72, start_datetime=forecast_start)
    forecast_pair['forecast'] = forecast_pair['forecast'].round(2)
    pair_forecasts[pair] = forecast_pair

# Calculate transfers & create recommendations
st.markdown("### Load Transfer Recommendations for Paired Feeders")
recommendations = []

for pair, forecast_pair in pair_forecasts.items():
    merged = pd.merge(main_forecast, forecast_pair, on='datetime', suffixes=(f'_{main_feeder}', f'_{pair}'))
    transfers, main_new, pair_new = [], [], []

    for _, row in merged.iterrows():
        main_a = row[f'forecast_{main_feeder}']
        pair_a = row[f'forecast_{pair}']
        if main_a > CAPACITY:
            over = main_a - CAPACITY
            space = max(0, CAPACITY - pair_a)
            transfer = min(over, space)
        else:
            transfer = 0
        transfers.append(round(transfer, 2))
        main_new.append(round(main_a - transfer, 2))
        pair_new.append(round(pair_a + transfer, 2))

    merged['transfer'] = transfers
    merged[f'adj_{main_feeder}'] = main_new
    merged[f'adj_{pair}'] = pair_new

    hours_over_after = ((merged[f'adj_{main_feeder}'] > CAPACITY) | (merged[f'adj_{pair}'] > CAPACITY)).sum()
    total_transfer = round(sum(transfers), 2)
    percent_safe = round((1 - hours_over_after / 72) * 100, 1)
    status = "Approved" if hours_over_after == 0 else ("Soft Approval" if percent_safe >= 90 else "Rejected")

    recommendations.append({
        "Primary Feeder": main_feeder.capitalize(),
        "Paired Feeder": pair.capitalize(),
        "Total Transfer (A)": total_transfer,
        "Safe Hours (%)": percent_safe,
        "Status": status
    })

# Display recommendations as metric cards
if recommendations:
    rec_df = pd.DataFrame(recommendations).sort_values("Safe Hours (%)", ascending=False).reset_index(drop=True)
    
    # Display top 3 recommendations as cards
    st.markdown("#### Top 3 Recommendations")
    cols = st.columns(min(3, len(rec_df)))
    
    for idx, col in enumerate(cols):
        if idx < len(rec_df):
            rec = rec_df.iloc[idx]
            status_class = "status-operational" if "Approved" in rec['Status'] else ("status-warning" if "Soft" in rec['Status'] else "status-reject")
            status_value_class = "status-value" if "Approved" in rec['Status'] else ("warning-value" if "Soft" in rec['Status'] else "reject-value")
            
            # Status icons
            status_icon = "✓" if "Approved" in rec['Status'] else ("⚠" if "Soft" in rec['Status'] else "✗")
            
            with col:
                st.markdown(f"""
                <div class="metric-card {status_class}">
                    <div class="metric-icon">{status_icon}</div>
                    <div class="metric-label">{rec['Paired Feeder']}</div>
                    <div class="{status_value_class}" style="font-size: 2.2em;">{rec['Safe Hours (%)']}%</div>
                    <div class="metric-status">{rec['Status']}</div>
                    <div style="color: #94a3b8; font-size: 0.85em; margin-top: 8px;">Transfer: {rec['Total Transfer (A)']} A</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Complete table with styling
    st.markdown("#### Complete Recommendation Table")
    st.dataframe(rec_df, use_container_width=True, height=350)
else:
    st.info("No viable feeder pairs available for load transfer.")

# ======================================================
# 📊 DETAILED TRANSFER ANALYSIS TABLE
# ======================================================
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-header">Detailed Transfer Analysis per Feeder</div>', unsafe_allow_html=True)

for pair, forecast_pair in pair_forecasts.items():
    merged = pd.merge(
        main_forecast, forecast_pair, on='datetime',
        suffixes=(f'_{main_feeder}', f'_{pair}')
    )

    transfers, main_new, pair_new = [], [], []

    for _, row in merged.iterrows():
        main_a = row[f'forecast_{main_feeder}']
        pair_a = row[f'forecast_{pair}']
        if main_a > CAPACITY:
            over = main_a - CAPACITY
            space = max(0, CAPACITY - pair_a)
            transfer = min(over, space)
        else:
            transfer = 0
        transfers.append(round(transfer, 2))
        main_new.append(round(main_a - transfer, 2))
        pair_new.append(round(pair_a + transfer, 2))

    merged['Transfer Load'] = transfers
    merged[f'Primary Before ({main_feeder})'] = merged[f'forecast_{main_feeder}']
    merged[f'Primary After ({main_feeder})'] = main_new
    merged[f'Target Before ({pair})'] = merged[f'forecast_{pair}']
    merged[f'Target After ({pair})'] = pair_new

    detail_table = merged[[
        'datetime',
        f'Primary Before ({main_feeder})',
        f'Primary After ({main_feeder})',
        f'Target Before ({pair})',
        f'Target After ({pair})',
        'Transfer Load'
    ]]

    st.markdown(f"""
    <div class="chart-container">
        <div style="font-size: 1.3em; font-weight: 700; color: #06b6d4; margin-bottom: 15px;">
            Transfer Details: {main_feeder.capitalize()} → {pair.capitalize()}
        </div>
    """, unsafe_allow_html=True)
    
    st.dataframe(detail_table, use_container_width=True, height=320)
    st.markdown('</div>', unsafe_allow_html=True)

# ======================================================
# 📈 FOOTER & SYSTEM INFO
# ======================================================
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-icon">⚡</div>
        <div class="metric-label">Total Feeders</div>
        <div class="metric-value" style="font-size: 2.5em;">16</div>
        <div class="metric-status">Active Network</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">📊</div>
        <div class="metric-label">Capacity Limit</div>
        <div class="metric-value" style="font-size: 2.5em;">{CAPACITY}A</div>
        <div class="metric-status">Max per Feeder</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    forecast_hours = 72 if "main_forecast" in st.session_state else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">🔮</div>
        <div class="metric-label">Forecast Range</div>
        <div class="metric-value" style="font-size: 2.5em;">{forecast_hours}h</div>
        <div class="metric-status">Prediction Window</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    data_points = len(data) if not data.empty else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">📈</div>
        <div class="metric-label">Historical Data</div>
        <div class="metric-value" style="font-size: 2.5em;">{data_points}</div>
        <div class="metric-status">Data Points</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 30px; background: rgba(15, 23, 42, 0.5); border-radius: 16px; border: 1px solid rgba(6, 182, 212, 0.2);">
    <p style="margin: 0; font-size: 1em; font-weight: 600; color: #94a3b8;">Advanced Load Distribution Forecasting System</p>
    <p style="margin: 8px 0 0 0; font-size: 0.85em;">Developed with Precision Engineering | Powered by Streamlit & Machine Learning</p>
    <p style="margin: 8px 0 0 0; font-size: 0.75em; color: #64748b;">Real-Time Historical Analysis & Predictive Load Balancing v2.0</p>
</div>
""", unsafe_allow_html=True)