import pandas as pd
import numpy as np
import pickle
import os

# ===============================
# CONFIG
# ===============================
MODEL_PATH = "models/model_Unibang.pkl"  


# ===============================
# LOAD MODEL
# ===============================
def load_model():
    """Load model pickle feeder Unibang"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model


# ===============================
# FITUR KHUSUS UNIBANG
# ===============================
def get_expected_level(hour: int) -> int:
    """Level ekspektasi beban berdasarkan jam (mapping dari notebook)"""
    level_map = {
        1: 32, 2: 32, 3: 32, 4: 32, 5: 32, 6: 35,
        7: 39, 8: 42, 9: 45, 10: 55,
        11: 64, 12: 65, 13: 64, 14: 65, 15: 64,
        16: 60, 17: 55, 18: 50,
        19: 45, 20: 42, 21: 39, 22: 37,
        23: 35, 0: 33
    }
    return level_map.get(hour, 40)


def create_unibang_features(df: pd.DataFrame) -> pd.DataFrame:
    """Buat exogenous features (harus sama dengan training)"""
    df_feat = pd.DataFrame(index=df.index)
    y = df['arus']

    # time-based features
    df_feat['hour'] = df.index.hour
    df_feat['dayofweek'] = df.index.dayofweek
    df_feat['is_weekend'] = (df_feat['dayofweek'] >= 5).astype(int)
    df_feat['night_constant'] = df_feat['hour'].between(1, 6).astype(int)
    df_feat['peak_constant'] = df_feat['hour'].between(11, 15).astype(int)
    df_feat['evening_decline'] = df_feat['hour'].between(19, 22).astype(int)
    df_feat['morning_rise'] = df_feat['hour'].between(6, 10).astype(int)
    df_feat['hour_sin'] = np.sin(2 * np.pi * df_feat['hour'] / 24)
    df_feat['hour_cos'] = np.cos(2 * np.pi * df_feat['hour'] / 24)

    # lag & rolling features
    df_feat['lag_1'] = y.shift(1)
    df_feat['lag_24'] = y.shift(24)
    df_feat['stability'] = (y.rolling(6).std() < y.std() * 0.5).astype(int)
    df_feat['expected_level'] = df_feat['hour'].apply(get_expected_level)

    # pastikan urutan kolom sama dengan saat training
    exog_vars = [
        'hour_sin', 'hour_cos', 'is_weekend',
        'night_constant', 'peak_constant', 'evening_decline', 'morning_rise',
        'lag_1', 'lag_24', 'stability', 'expected_level'
    ]
    return df_feat[exog_vars].fillna(method='bfill').fillna(method='ffill')


# ===============================
# FUNGSI FORECAST
# ===============================
def forecast(df_historical: pd.DataFrame, steps: int = 72, start_datetime=None) -> pd.DataFrame:
    """
    Forecast arus 72 jam ke depan untuk feeder Unibang.
    df_historical: DataFrame dengan kolom 'arus' dan index datetime
    """
    model = load_model()

    if 'arus' not in df_historical.columns:
        raise ValueError("DataFrame harus memiliki kolom 'arus'.")

    df_historical = df_historical.sort_index()
    if start_datetime is None:
        start_datetime = df_historical.index.max() + pd.Timedelta(hours=1)

    # Buat indeks waktu ke depan
    future_index = pd.date_range(start=start_datetime, periods=steps, freq='H')

    # Siapkan exogenous features
    try:
        exog = create_unibang_features(df_historical)
        exog_future = exog.iloc[-steps:] if len(exog) >= steps else exog
        forecast_values = model.forecast(steps=steps, exog=exog_future)
    except Exception as e:
        print(f"[Warning] Forecast Unibang gagal pakai exog ({e}), mencoba tanpa exog..")
        forecast_values = model.forecast(steps=steps)

    forecast_df = pd.DataFrame({
        'datetime': future_index,
        'forecast': np.round(forecast_values, 2)
    })
    return forecast_df
