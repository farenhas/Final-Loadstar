import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go
from utils.db_util import get_unique_feeders, get_historical_data

# ==================== CONFIG ====================
st.set_page_config(page_title="⚡ Historical Load Monitor", layout="wide", page_icon="⚙️")

st.title("⚡ Historical Load Monitor")
st.markdown("Sistem prediksi dan analisis pelimpahan beban antar feeder")

# ==================== SIDEBAR ====================
st.sidebar.header("⚙️ Pengaturan")

feeders = sorted(get_unique_feeders())
selected_feeder = st.sidebar.selectbox("Pilih Feeder Utama", feeders)
start_date = st.sidebar.date_input("Dari tanggal", datetime.now() - timedelta(days=7))
end_date = st.sidebar.date_input("Sampai tanggal", datetime.now())

# ==================== LOAD DATA ====================
@st.cache_data
def load_data(feeder, start, end):
    df = get_historical_data(feeder, start, end)
    if df.empty:
        return df
    df['jam_order'] = df['jam'].apply(lambda x: int(x.split('_')[0]) * 60)
    df = df.sort_values(by=['tanggal', 'jam_order']).drop(columns=['jam_order'])
    return df

data = load_data(selected_feeder, start_date, end_date)

# ==================== STEP 1: FORECAST FEEDER UTAMA ====================
st.markdown("## 🔮 Step 1 — Forecast Feeder Utama")

if data.empty:
    st.warning("Tidak ada data historis untuk feeder ini.")
    st.stop()

forecast_btn = st.button("🚀 Jalankan Forecast Feeder Utama", use_container_width=True)

if forecast_btn:
    with st.spinner("Melakukan forecast..."):
        time.sleep(0.5)
        try:
            feeder_module = __import__(f"feeders.{selected_feeder.lower()}", fromlist=['forecast'])
        except ModuleNotFoundError:
            st.error(f"Model untuk feeder `{selected_feeder}` belum tersedia.")
            st.stop()

        df_hist = data[['datetime', 'arus']].set_index('datetime')
        forecast_start = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        forecast_df = feeder_module.forecast(df_hist, steps=72, start_datetime=forecast_start)
        forecast_df['forecast'] = forecast_df['forecast'].round(2)

        st.session_state["main_forecast"] = {"feeder": selected_feeder, "data": forecast_df}

    st.success(f"Forecast feeder {selected_feeder} selesai ✅")

    st.markdown(f"### 📈 Hasil Forecast Feeder {selected_feeder}")
    st.dataframe(forecast_df, use_container_width=True, height=250)

    fig_main = go.Figure()
    fig_main.add_trace(go.Scatter(x=df_hist.index, y=df_hist['arus'], name="Historis", mode="lines"))
    fig_main.add_trace(go.Scatter(
        x=forecast_df['datetime'], y=forecast_df['forecast'],
        name="Forecast 72 Jam", mode="lines+markers", line=dict(color="orange", dash="dot")
    ))
    fig_main.update_layout(
        xaxis_title="Datetime", yaxis_title="Arus (A)",
        template="plotly_dark", height=400
    )
    st.plotly_chart(fig_main, use_container_width=True)

# ==================== STEP 2: ANALISIS PELIMPAHAN ====================
st.markdown("---")
st.markdown("## 🔗 Step 2 — Analisis Pelimpahan Beban")

if "main_forecast" not in st.session_state:
    st.info("Lakukan forecast feeder utama terlebih dahulu.")
    st.stop()

main_feeder = st.session_state["main_forecast"]["feeder"]
main_forecast = st.session_state["main_forecast"]["data"]

# Hardcoded pasangan feeder
feeder_pairs = {
    "tragah": ["labang", "alang"],
    "labang": ["tragah"],
}
possible_pairs = feeder_pairs.get(main_feeder.lower(), [])

if not possible_pairs:
    st.warning("Feeder ini belum memiliki pasangan pelimpahan.")
    st.stop()

selected_pairs = st.multiselect("Pilih feeder pasangan untuk analisis:", possible_pairs)

if st.button("📊 Jalankan Analisis Pelimpahan", use_container_width=True):
    if not selected_pairs:
        st.info("Pilih minimal satu feeder pasangan.")
        st.stop()

    results = []
    progress = st.progress(0)

    for idx, pair in enumerate(selected_pairs):
        progress.progress((idx + 1) / len(selected_pairs))
        time.sleep(0.5)
        st.markdown(f"### 🔍 Analisis Feeder {pair.capitalize()}")

        try:
            pair_module = __import__(f"feeders.{pair}", fromlist=['forecast'])
        except ModuleNotFoundError:
            st.warning(f"Feeder {pair} belum memiliki model forecast.")
            continue

        df_pair_hist = load_data(pair, start_date, end_date)
        if df_pair_hist.empty:
            st.warning(f"Tidak ada data historis untuk feeder {pair}.")
            continue

        df_pair_hist = df_pair_hist[['datetime', 'arus']].set_index('datetime')
        forecast_start = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        forecast_pair = pair_module.forecast(df_pair_hist, steps=72, start_datetime=forecast_start)
        forecast_pair['forecast'] = forecast_pair['forecast'].round(2)

        st.dataframe(forecast_pair, use_container_width=True, height=250)

        fig_pair = go.Figure()
        fig_pair.add_trace(go.Scatter(x=df_pair_hist.index, y=df_pair_hist['arus'], mode="lines", name="Historis"))
        fig_pair.add_trace(go.Scatter(
            x=forecast_pair['datetime'], y=forecast_pair['forecast'],
            mode="lines+markers", name="Forecast", line=dict(color="lime", dash="dot")
        ))
        fig_pair.update_layout(template="plotly_dark", height=300)
        st.plotly_chart(fig_pair, use_container_width=True)

        # Gabungkan hasil forecast dua feeder
        merged = pd.merge(
            main_forecast, forecast_pair,
            on='datetime', suffixes=(f'_{main_feeder}', f'_{pair}')
        )
        merged['total'] = merged[f'forecast_{main_feeder}'] + merged[f'forecast_{pair}']
        max_load = merged['total'].max()
        mean_load = merged['total'].mean()

        status = (
            "✅ Aman" if max_load < 380 else
            "⚠️ Mendekati Batas" if max_load < 400 else
            "🔴 Overload"
        )

        results.append({
            "Feeder Utama": main_feeder.capitalize(),
            "Feeder Pasangan": pair.capitalize(),
            "Rata-rata Total (A)": round(mean_load, 2),
            "Maksimum Total (A)": round(max_load, 2),
            "Status": status
        })

    st.success("Analisis pelimpahan selesai ✅")

    if results:
        st.markdown("### 📘 Ringkasan Analisis Pelimpahan")
        result_df = pd.DataFrame(results).sort_values("Maksimum Total (A)").reset_index(drop=True)
        st.dataframe(result_df, use_container_width=True)
        st.markdown(
            "<small>Tabel diurutkan dari total beban terendah (paling direkomendasikan) ke tertinggi.</small>",
            unsafe_allow_html=True
        )
