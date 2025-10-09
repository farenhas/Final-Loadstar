import pandas as pd
import numpy as np
import pickle
import os

MODEL_PATH = "models/model_Torjun.pkl"

# =====================================================
# LOAD MODEL
# =====================================================
def load_model():
    """Load model pickle feeder Torjun"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file tidak ditemukan: {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model


# =====================================================
# FEATURE ENGINEERING
# =====================================================
def create_torjun_features(datetime_index):
    """Generate exogenous features untuk feeder Torjun"""
    df_feat = pd.DataFrame(index=datetime_index)
    df_feat["hour"] = datetime_index.hour
    df_feat["dayofweek"] = datetime_index.dayofweek

    # Waktu harian
    df_feat["is_morning"] = df_feat["hour"].between(6, 8).astype(int)
    df_feat["is_afternoon"] = df_feat["hour"].between(12, 14).astype(int)
    df_feat["is_evening_peak"] = df_feat["hour"].between(17, 19).astype(int)
    df_feat["is_evening_decline"] = df_feat["hour"].between(20, 22).astype(int)
    df_feat["is_night"] = ((df_feat["hour"] >= 23) | (df_feat["hour"] <= 5)).astype(int)

    # Hari dalam minggu
    df_feat["is_weekend"] = (df_feat["dayofweek"] >= 5).astype(int)
    df_feat["is_monday"] = (df_feat["dayofweek"] == 0).astype(int)
    df_feat["is_friday"] = (df_feat["dayofweek"] == 4).astype(int)

    # Fitur siklik
    df_feat["hour_sin"] = np.sin(2 * np.pi * df_feat["hour"] / 24)
    df_feat["hour_cos"] = np.cos(2 * np.pi * df_feat["hour"] / 24)
    df_feat["dow_sin"] = np.sin(2 * np.pi * df_feat["dayofweek"] / 7)
    df_feat["dow_cos"] = np.cos(2 * np.pi * df_feat["dayofweek"] / 7)

    # Kombinasi perilaku
    df_feat["weekend_evening"] = (df_feat["is_weekend"] * df_feat["is_evening_peak"]).astype(int)
    df_feat["monday_morning"] = (df_feat["is_monday"] * df_feat["is_morning"]).astype(int)

    # Pastikan urutan kolom sama dengan saat training
    feature_cols = [
        "is_morning", "is_afternoon", "is_evening_peak", "is_evening_decline", "is_night",
        "is_weekend", "is_monday", "is_friday",
        "hour_sin", "hour_cos", "dow_sin", "dow_cos",
        "weekend_evening", "monday_morning"
    ]

    return df_feat[feature_cols]


# =====================================================
# FORECAST FUNCTION
# =====================================================
def forecast(df_historical, steps=72, start_datetime=None):
    """
    Forecast arus 72 jam ke depan untuk feeder Torjun.
    df_historical: DataFrame dengan kolom 'arus' dan index datetime
    """
    model = load_model()

    # Tentukan waktu mulai
    if start_datetime is None:
        start_datetime = df_historical.index.max() + pd.Timedelta(hours=1)

    # Buat future index
    future_index = pd.date_range(start=start_datetime, periods=steps, freq="H")

    # Siapkan exogenous variables
    exog = create_torjun_features(future_index)

    # Lakukan forecasting
    try:
        forecast_values = model.forecast(steps=steps, exog=exog)
    except Exception as e:
        print(f"Warning: Forecast dengan exog gagal ({e}), mencoba tanpa exog.")
        forecast_values = model.forecast(steps=steps)

    # Kembalikan hasil sebagai DataFrame
    forecast_df = pd.DataFrame({
        "datetime": future_index,
        "forecast": np.round(forecast_values, 2)
    })

    return forecast_df
