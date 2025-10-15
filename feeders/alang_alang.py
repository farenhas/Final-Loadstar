import pandas as pd
import numpy as np
import pickle
import os

MODEL_PATH = "models/model_alang_alang.pkl"

FORECAST_HORIZON = 72
HISTORY_LENGTH = 1440


def load_model():
    """Load model SARIMA feeder Alang dari file pickle."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file tidak ditemukan: {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model


def forecast(df_historical, steps=FORECAST_HORIZON, start_datetime=None):

    model = load_model()

    if not isinstance(df_historical.index, pd.DatetimeIndex):
        raise ValueError("df_historical harus memiliki index bertipe datetime")

    df_historical = df_historical.tail(HISTORY_LENGTH).copy()

    if start_datetime is None:
        start_datetime = df_historical.index.max() + pd.Timedelta(hours=1)

    future_index = pd.date_range(start=start_datetime, periods=steps, freq="H")

    forecast_values = model.forecast(steps=steps)

    forecast_df = pd.DataFrame({
        "datetime": future_index,
        "forecast": np.maximum(forecast_values, 0).round(2)
    })

    return forecast_df
 