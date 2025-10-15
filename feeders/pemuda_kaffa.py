import pandas as pd
import numpy as np
import pickle
import os

MODEL_PATH = "models/model_pemuda_kaffa.pkl"

FORECAST_HORIZON = 72
HISTORY_LENGTH = 1440

# ======================================================
# 🔹 Fungsi utilitas
# ======================================================

def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file tidak ditemukan: {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model


def prepare_exog(index):
    df = pd.DataFrame(index=index)

    # Tambahkan fitur waktu
    df['hour'] = df.index.hour
    df['dayofweek'] = df.index.dayofweek   # Senin=0, Minggu=6
    df['is_weekend'] = df['dayofweek'].apply(lambda x: 1 if x >= 5 else 0)
    df['is_midnight'] = df['hour'].apply(lambda x: 1 if (0 <= x <= 4) else 0)
    df['is_morning_drop'] = df['hour'].apply(lambda x: 1 if (5 <= x <= 8) else 0)
    return df[['is_weekend', 'is_midnight', 'is_morning_drop']]


def forecast(df_historical, steps=FORECAST_HORIZON, start_datetime=None):
    model = load_model()

    if not isinstance(df_historical.index, pd.DatetimeIndex):
        raise ValueError("df_historical harus memiliki index bertipe datetime")

    df_historical = df_historical.tail(HISTORY_LENGTH).copy()

    if start_datetime is None:
        start_datetime = df_historical.index.max() + pd.Timedelta(hours=1)

    future_index = pd.date_range(start=start_datetime, periods=steps, freq="H")

    exog_future = prepare_exog(future_index)

    forecast_values = model.forecast(steps=steps, exog=exog_future)

    forecast_df = pd.DataFrame({
        "datetime": future_index,
        "forecast": np.maximum(forecast_values, 0).round(2)
    })
    return forecast_df
