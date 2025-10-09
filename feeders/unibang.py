import pandas as pd
import numpy as np
import pickle
import os

MODEL_PATH = "models/model_unibang.pkl"
FORECAST_HORIZON = 72
HISTORY_LENGTH = 1440 

# ======================================================
# 🔹 Fungsi utilitas
# ======================================================

def load_model():
    """Muat model SARIMAX Unibang dari file pickle"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file tidak ditemukan: {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model


def get_expected_level(hour):
    """Level arus nominal berdasarkan jam"""
    level_map = {
        1: 32, 2: 32, 3: 32, 4: 32, 5: 32, 6: 35,
        7: 39, 8: 42, 9: 45, 10: 55,
        11: 64, 12: 65, 13: 64, 14: 65, 15: 64,
        16: 60, 17: 55, 18: 50,
        19: 45, 20: 42, 21: 39, 22: 37,
        23: 35, 0: 33
    }
    return level_map.get(hour, 40)


def prepare_exog(index):
    """Buat fitur exogenous untuk indeks waktu tertentu"""
    df = pd.DataFrame(index=index)
    df["hour"] = df.index.hour
    df["dayofweek"] = df.index.dayofweek

    # --- Fitur waktu & musiman ---
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)
    df["night_constant"] = df["hour"].between(1, 6).astype(int)
    df["peak_constant"] = df["hour"].between(11, 15).astype(int)
    df["evening_decline"] = df["hour"].between(19, 22).astype(int)
    df["morning_rise"] = df["hour"].between(6, 10).astype(int)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

    # --- Placeholder lag & statistik (isi 0 karena future) ---
    df["lag_1"] = 0
    df["lag_24"] = 0
    df["stability"] = 1
    df["expected_level"] = df["hour"].apply(get_expected_level)

    # --- Urutan kolom sesuai model ---
    cols = [
        "hour_sin","hour_cos","is_weekend",
        "night_constant","peak_constant","evening_decline","morning_rise",
        "lag_1","lag_24","stability","expected_level"
    ]
    return df[cols]


# ======================================================
# 🔹 Fungsi utama forecasting
# ======================================================

def forecast(df_historical, steps=FORECAST_HORIZON, start_datetime=None):
    """
    Forecast arus feeder Unibang untuk beberapa jam ke depan.
    df_historical: DataFrame historis (index datetime, kolom 'arus')
    steps: jumlah jam ke depan
    start_datetime: waktu mulai forecast (default = max index + 1 jam)
    """
    model = load_model()

    if not isinstance(df_historical.index, pd.DatetimeIndex):
        raise ValueError("df_historical harus memiliki index bertipe datetime")

    df_historical = df_historical.tail(HISTORY_LENGTH).copy()

    if start_datetime is None:
        start_datetime = df_historical.index.max() + pd.Timedelta(hours=1)

    future_index = pd.date_range(start=start_datetime, periods=steps, freq="H")

    # --- Buat exogenous features untuk periode forecast ---
    exog_future = prepare_exog(future_index)

    # --- Prediksi menggunakan model ---
    forecast_values = model.forecast(steps=steps, exog=exog_future)

    forecast_df = pd.DataFrame({
        "datetime": future_index,
        "forecast": np.maximum(forecast_values, 0).round(2)
    })
    return forecast_df
