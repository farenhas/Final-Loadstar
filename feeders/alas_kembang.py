import pandas as pd
import numpy as np
import pickle
import os

MODEL_PATH = "models/model_alas_kembang.pkl"

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
    df["hour"] = df.index.hour
    df["is_peak_evening"] = df["hour"].apply(lambda x: 1 if (18 <= x <= 23) else 0)
    df["is_peak_midnight"] = df["hour"].apply(lambda x: 1 if (x == 0 or x == 1) else 0)
    df["is_midmorning"] = df["hour"].apply(lambda x: 1 if (9 <= x <= 12) else 0)
    df["is_prepeak"] = df["hour"].apply(lambda x: 1 if (16 <= x <= 17) else 0)
    return df[["is_peak_evening", "is_peak_midnight", "is_midmorning", "is_prepeak"]]


# ======================================================
# 🔹 Fungsi utama forecasting
# ======================================================

def forecast(df_historical, steps=FORECAST_HORIZON, start_datetime=None):
    """
    Forecast arus feeder Alas Kembang untuk beberapa jam ke depan.
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

    exog_future = prepare_exog(future_index)

    forecast_values = model.forecast(steps=steps, exog=exog_future)

    forecast_df = pd.DataFrame({
        "datetime": future_index,
        "forecast": np.maximum(forecast_values, 0).round(2)
    })
    return forecast_df
