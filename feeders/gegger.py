import pandas as pd
import numpy as np
import pickle
import os
from datetime import timedelta

# === CONFIGURASI ===
TARGET_FEEDER = "Gegger"
MODEL_PATH = "models/model_Gegger.pkl"
FORECAST_HORIZON = 72  # jam ke depan

# === 1. Load model ===
def load_model():
    """Load model SARIMAX Gegger"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file tidak ditemukan: {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model

# === 2. Feature engineering untuk Gegger ===
def get_time_period(hour):
    if 6 <= hour <= 11:
        return 'pagi'
    elif 12 <= hour <= 17:
        return 'siang'
    elif 18 <= hour <= 23:
        return 'sore_malam'
    else:
        return 'dini_hari'

def create_gegger_features(datetime_index, historical_data=None):
    """Bangun semua fitur exogenous sesuai karakteristik Gegger"""
    df_feat = pd.DataFrame(index=datetime_index)
    df_feat["time_period"] = datetime_index.hour.map(get_time_period)
    df_feat["weekday"] = datetime_index.weekday

    # --- Pola khas Gegger ---
    df_feat["sabtu_sore_malam"] = ((df_feat["weekday"] == 5) &
                                   (df_feat["time_period"] == "sore_malam")).astype(int) * 2
    df_feat["kamis_siang_sore"] = ((df_feat["weekday"] == 3) &
                                   (df_feat["time_period"].isin(["siang", "sore_malam"]))).astype(int) * 3
    df_feat["minggu_siang"] = ((df_feat["weekday"] == 6) &
                               (df_feat["time_period"] == "siang")).astype(int) * 2
    df_feat["selasa_pagi_sore"] = ((df_feat["weekday"] == 1) &
                                   (df_feat["time_period"].isin(["pagi", "siang", "sore_malam"]))).astype(int) * 3
    df_feat["jumat_pagi_sore"] = ((df_feat["weekday"] == 4) &
                                  (df_feat["time_period"].isin(["pagi", "siang", "sore_malam"]))).astype(int) * 4
    df_feat["rabu_pagi_sore"] = ((df_feat["weekday"] == 2) &
                                 (df_feat["time_period"].isin(["pagi", "siang", "sore_malam"]))).astype(int) * 2

    # Pola umum waktu
    df_feat["is_peak_sore_malam"] = (df_feat["time_period"] == "sore_malam").astype(int)
    df_feat["is_low_dini_hari"] = (df_feat["time_period"] == "dini_hari").astype(int)
    df_feat["is_transition_pagi"] = (df_feat["time_period"] == "pagi").astype(int)

    # === Pola probabilistik drop & spike ===
    if historical_data is not None and len(historical_data) > 24:
        recent = historical_data.tail(1440)
        extreme_drop_rate = (recent < 25).mean()
        spike_rate = ((recent > 85) & (recent.shift(1) < 30)).mean()
        volatility_factor = recent.std() / max(recent.mean(), 1)
    else:
        extreme_drop_rate = 0.08
        spike_rate = 0.05
        volatility_factor = 0.4

    np.random.seed(hash(str(datetime_index[0])) % (2**32))

    drop_multiplier = np.where(
        df_feat["jumat_pagi_sore"] > 0, 3.0,
        np.where(df_feat["kamis_siang_sore"] > 0, 2.5,
        np.where(df_feat["rabu_pagi_sore"] > 0, 2.0,
        np.where(df_feat["selasa_pagi_sore"] > 0, 1.8, 1.0)))
    )
    base_drop_prob = extreme_drop_rate * drop_multiplier * volatility_factor
    df_feat["is_extreme_drop"] = (np.random.random(len(datetime_index)) < base_drop_prob).astype(int)

    spike_cond = (
        (df_feat["is_extreme_drop"].shift(1, fill_value=0) > 0) |
        (df_feat["sabtu_sore_malam"] > 0) |
        ((df_feat["weekday"].isin([0,1,2,3,4])) & (df_feat["time_period"] == "sore_malam"))
    )
    spike_prob = np.where(spike_cond, spike_rate * 2, spike_rate * 0.5)
    df_feat["is_recovery_spike"] = (np.random.random(len(datetime_index)) < spike_prob).astype(int)

    return df_feat

# === 3. Forecast function utama ===
def forecast(df_historical, steps=FORECAST_HORIZON, start_datetime=None):
    """
    df_historical: DataFrame historis arus (datetime index)
    steps: jumlah jam ke depan untuk forecast
    start_datetime: waktu mulai forecast (default = last timestamp + 1 jam)
    """
    if not isinstance(df_historical, pd.DataFrame):
        df_historical = pd.DataFrame(df_historical, columns=["arus"])
    df_historical = df_historical.sort_index()
    model = load_model()

    # --- Tentukan waktu mulai forecast ---
    if start_datetime is None:
        start_datetime = df_historical.index.max() + pd.Timedelta(hours=1)

    # --- Buat indeks waktu ke depan ---
    future_index = pd.date_range(start=start_datetime, periods=steps, freq="H")

    # --- Buat fitur exogenous untuk periode forecast ---
    future_features = create_gegger_features(future_index, historical_data=df_historical["arus"])

    # --- Urutan prioritas fitur ---
    primary_exog = [
        "sabtu_sore_malam","kamis_siang_sore","minggu_siang",
        "selasa_pagi_sore","jumat_pagi_sore","rabu_pagi_sore",
        "is_peak_sore_malam","is_low_dini_hari","is_extreme_drop","is_recovery_spike"
    ]
    simple_exog = ["jumat_pagi_sore","kamis_siang_sore","is_extreme_drop","is_recovery_spike"]
    fallback_exog = ["is_extreme_drop","is_recovery_spike"]

    # --- Multi-level forecast attempt ---
    for exog_list in [primary_exog, simple_exog, fallback_exog, []]:
        try:
            if exog_list:
                missing = [v for v in exog_list if v not in future_features.columns]
                if missing:
                    continue
                exog_data = future_features[exog_list].fillna(0)
                forecast_vals = model.forecast(steps=steps, exog=exog_data)
            else:
                forecast_vals = model.forecast(steps=steps)

            forecast_df = pd.DataFrame({
                "datetime": future_index,
                "forecast": np.maximum(forecast_vals, 0).round(2)
            })
            return forecast_df
        except Exception:
            continue

    raise RuntimeError("Semua percobaan forecast gagal untuk Gegger")
