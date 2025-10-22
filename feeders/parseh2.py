import pandas as pd
import numpy as np
import pickle
import os

MODEL_PATH = "models/model_parseh.pkl"
FORECAST_HORIZON = 72
HISTORY_LENGTH = 1440


def load_model():
    """Load model pickle feeder Parseh"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    
    with open(MODEL_PATH, "rb") as f:
        data = pickle.load(f)
    
    # Pastikan struktur sesuai dengan yang disimpan
    model_fit = data["model_fit"]
    exog_cols = data["exog_cols"]
    
    return model_fit, exog_cols


def prepare_exog(index):
    """Siapkan fitur eksogen berdasarkan waktu"""
    df = pd.DataFrame(index=index)
    df['hour'] = df.index.hour
    df['is_7to12'] = df['hour'].apply(lambda x: 1 if 7 <= x <= 12 else 0)
    df['is_18to22'] = df['hour'].apply(lambda x: 1 if 18 <= x <= 22 else 0)
    df['dayofweek'] = df.index.dayofweek
    return df[['is_7to12', 'is_18to22', 'dayofweek']]


def forecast(df_historical, steps=FORECAST_HORIZON, start_datetime=None):
    """Lakukan forecast berdasarkan model SARIMAX"""
    model_fit, exog_cols = load_model()

    if not isinstance(df_historical.index, pd.DatetimeIndex):
        raise ValueError("df_historical harus memiliki index bertipe datetime")

    # Ambil HISTORY_LENGTH terakhir
    df_historical = df_historical.tail(HISTORY_LENGTH).copy()

    # Tentukan waktu mulai prediksi
    if start_datetime is None:
        start_datetime = df_historical.index.max() + pd.Timedelta(hours=1)

    # Buat index waktu prediksi
    future_index = pd.date_range(start=start_datetime, periods=steps, freq="H")

    # Siapkan exogenous sesuai struktur model
    exog_future = prepare_exog(future_index)[exog_cols]

    # Gunakan model_fit untuk forecast
    forecast_values = model_fit.forecast(steps=steps, exog=exog_future)

    # Bungkus ke DataFrame
    forecast_df = pd.DataFrame({
        "datetime": future_index,
        "forecast": np.maximum(forecast_values, 0).round(2)
    })

    return forecast_df
