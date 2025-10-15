import pandas as pd
import numpy as np
import pickle
import os

MODEL_PATH = "models/model_tanah_merah.pkl"

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
    df['hour'] = df.index.hour
    df['hour'] = df.index.hour
    df['dayofweek'] = df.index.dayofweek   
    df['day'] = df.index.day
    df['month'] = df.index.month
    
    df['is_weekend'] = df['dayofweek'].apply(lambda x: 1 if x >= 5 else 0)
    df['is_morning_peak'] = df['hour'].apply(lambda x: 1 if (7 <= x <= 9) else 0)     # Jam sibuk pagi
    df['is_afternoon_dip'] = df['hour'].apply(lambda x: 1 if (13 <= x <= 15) else 0)  # Jam penurunan siang
    df['is_evening_peak'] = df['hour'].apply(lambda x: 1 if (17 <= x <= 19) else 0)   # Jam sibuk sore
    df['is_night'] = df['hour'].apply(lambda x: 1 if (22 <= x <= 23) or (0 <= x <= 5) else 0)  # Malam

    # 3. Pola hari kerja vs weekend yang lebih spesifik
    df['monday'] = (df['dayofweek'] == 0).astype(int)        # Senin biasanya beda
    df['friday'] = (df['dayofweek'] == 4).astype(int)        # Jumat juga beda
    df['weekend_afternoon'] = ((df['is_weekend'] == 1) & (df['is_afternoon_dip'] == 1)).astype(int)

    # 4. Interaksi antara hari dan jam (untuk pola yang lebih kompleks)
    df['weekday_afternoon'] = ((df['is_weekend'] == 0) & (df['is_afternoon_dip'] == 1)).astype(int)

    return df[['is_weekend', 'is_morning_peak', 'is_afternoon_dip', 'is_evening_peak', 'is_night',
    'monday', 'friday', 'weekend_afternoon', 'weekday_afternoon']]


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
