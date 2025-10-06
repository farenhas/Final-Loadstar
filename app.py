import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go
from utils.db_util import get_unique_feeders, get_historical_data

# ======================================================
# ⚙️ KONFIGURASI DASAR
# ======================================================
st.set_page_config(page_title="⚡ Historical Load Monitor", layout="wide", page_icon="⚙️")
st.title("⚡ Historical Load Monitor")
st.markdown("Sistem prediksi dan analisis pelimpahan beban antar feeder")

# ======================================================
# 🎚️ PENGATURAN SIDEBAR
# ======================================================
st.sidebar.header("⚙️ Pengaturan")
feeders = sorted(get_unique_feeders())
selected_feeder = st.sidebar.selectbox("Pilih Feeder Utama", feeders)
start_date = st.sidebar.date_input("Dari tanggal", datetime.now() - timedelta(days=7))
end_date = st.sidebar.date_input("Sampai tanggal", datetime.now())
simulate_overload = st.sidebar.checkbox("💥 Simulasikan Overload (uji pelimpahan)", value=False)
dummy_boost = 250 if simulate_overload else 0
CAPACITY = 400

# ======================================================
# 📊 LOAD DATA HISTORIS
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
st.markdown("## 📘 Data Historis")
if data.empty:
    st.warning("Tidak ada data historis untuk feeder ini pada rentang tanggal yang dipilih.")
    st.stop()
st.success(f"Menampilkan data feeder **{selected_feeder}** dari **{start_date}** hingga **{end_date}**.")
st.dataframe(data[['datetime', 'arus']], use_container_width=True, height=250)

# GRAFIK HISTORIS
fig_hist = go.Figure()
fig_hist.add_trace(go.Scatter(x=data['datetime'], y=data['arus'], mode='lines+markers', name='Arus Historis', line=dict(color='cyan')))
fig_hist.update_layout(title=f"Arus Historis Feeder {selected_feeder}", xaxis_title="Datetime", yaxis_title="Arus (A)", template="plotly_dark", height=400)
st.plotly_chart(fig_hist, use_container_width=True)

# ======================================================
# 🔮 STEP 1: FORECAST FEEDER UTAMA
# ======================================================
st.markdown("---")
st.markdown("## 🔮 Step 1 — Forecast Feeder Utama")
forecast_btn = st.button("🚀 Jalankan Forecast Feeder Utama", use_container_width=True)

if forecast_btn:
    with st.spinner("Melakukan forecast..."):
        try:
            feeder_module = __import__(f"feeders.{selected_feeder.lower()}", fromlist=['forecast'])
        except ModuleNotFoundError:
            st.error(f"Model untuk feeder {selected_feeder} belum tersedia.")
            st.stop()
        
        df_hist = data[['datetime', 'arus']].set_index('datetime')
        forecast_start = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        forecast_df = feeder_module.forecast(df_hist, steps=72, start_datetime=forecast_start)
        forecast_df['forecast'] = forecast_df['forecast'].round(2)
        if simulate_overload:
            forecast_df['forecast'] += dummy_boost
            st.warning(f"Simulasi overload aktif — menambah {dummy_boost} A pada seluruh titik forecast.")
        
        st.session_state["main_forecast"] = {"feeder": selected_feeder, "data": forecast_df}
        st.success(f"Forecast feeder {selected_feeder} selesai ✅")
        st.dataframe(forecast_df, use_container_width=True, height=250)

        fig_main = go.Figure()
        fig_main.add_trace(go.Scatter(x=df_hist.index, y=df_hist['arus'], name="Historis", mode="lines"))
        fig_main.add_trace(go.Scatter(x=forecast_df['datetime'], y=forecast_df['forecast'], name="Forecast 72 Jam", mode="lines+markers", line=dict(color="orange", dash="dot")))
        fig_main.add_hline(y=CAPACITY, line_dash="dot", line_color="red", annotation_text="Batas 400A")
        fig_main.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig_main, use_container_width=True)

# ======================================================
# 🔗 STEP 2: ANALISIS PELIMPAHAN & REKOMENDASI
# ======================================================
st.markdown("---")
st.markdown("## 🔗 Step 2 — Analisis Pelimpahan & Rekomendasi")

if "main_forecast" not in st.session_state:
    st.info("Lakukan forecast feeder utama terlebih dahulu.")
    st.stop()

main_feeder = st.session_state["main_forecast"]["feeder"]
main_forecast = st.session_state["main_forecast"]["data"]

# FEEDER PAIR DEFINISI
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

# Buat dua arah otomatis
for asal, tujuan_list in list(feeder_pairs.items()):
    for tujuan in tujuan_list:
        feeder_pairs.setdefault(tujuan.lower(), [])
        if asal.lower() not in feeder_pairs[tujuan.lower()]:
            feeder_pairs[tujuan.lower()].append(asal.lower())

possible_pairs = feeder_pairs.get(main_feeder.lower(), [])
if not possible_pairs:
    st.warning("Feeder ini belum memiliki pasangan pelimpahan.")
    st.stop()

# Forecast semua feeder pasangan dulu
st.markdown("### 🔮 Forecast Semua Feeder Pasangan")
pair_forecasts = {}
for pair in possible_pairs:
    try:
        pair_module = __import__(f"feeders.{pair.lower()}", fromlist=['forecast'])
    except ModuleNotFoundError:
        st.warning(f"Model untuk feeder {pair} belum tersedia. Lewati.")
        continue
    df_pair_hist = load_data(pair, start_date, end_date)
    if df_pair_hist.empty:
        st.warning(f"Tidak ada data historis untuk feeder {pair}. Lewati.")
        continue
    df_pair_hist = df_pair_hist[['datetime', 'arus']].set_index('datetime')
    forecast_pair = pair_module.forecast(df_pair_hist, steps=72, start_datetime=forecast_start)
    forecast_pair['forecast'] = forecast_pair['forecast'].round(2)
    pair_forecasts[pair] = forecast_pair

# ======================================================
# Hitung pelimpahan & buat rekomendasi
# ======================================================
st.markdown("### ⚙️ Rekomendasi Pelimpahan Feeder Pasangan")
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
    status = "✅ Approved" if hours_over_after == 0 else ("⚠️ Soft-GO" if percent_safe >= 90 else "❌ Reject")

    recommendations.append({
        "Feeder Utama": main_feeder.capitalize(),
        "Feeder Pasangan": pair.capitalize(),
        "Total Arus Dipindahkan (A)": total_transfer,
        "Persen Jam Aman (%)": percent_safe,
        "Status": status
    })

# Tampilkan rekomendasi
if recommendations:
    rec_df = pd.DataFrame(recommendations).sort_values("Persen Jam Aman (%)", ascending=False).reset_index(drop=True)
    st.dataframe(rec_df, use_container_width=True)
else:
    st.info("Tidak ada rekomendasi feeder pasangan yang memungkinkan.")

# ======================================================
# 📊 TABEL ANALISIS DETAIL
# ======================================================
st.markdown("### 📊 Analisis Detail Pelimpahan per Feeder")

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

    merged['Arus Dilimpahkan'] = transfers
    merged[f'Utama Sebelum ({main_feeder})'] = merged[f'forecast_{main_feeder}']
    merged[f'Utama Sesudah ({main_feeder})'] = main_new
    merged[f'Tujuan Sebelum ({pair})'] = merged[f'forecast_{pair}']
    merged[f'Tujuan Sesudah ({pair})'] = pair_new

    detail_table = merged[[
        'datetime',
        f'Utama Sebelum ({main_feeder})',
        f'Utama Sesudah ({main_feeder})',
        f'Tujuan Sebelum ({pair})',
        f'Tujuan Sesudah ({pair})',
        'Arus Dilimpahkan'
    ]]

    st.markdown(f"#### 🔄 Detail Pelimpahan — {main_feeder.capitalize()} ➝ {pair.capitalize()}")
    st.dataframe(detail_table, use_container_width=True, height=300)
