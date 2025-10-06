import pandas as pd
import numpy as np
import pickle
import os

MODEL_PATH = "models/model_unibang.pkl"

def load_model():
    """Load model pickle feeder Unibang"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model


def get_expected_level(hour):
    """Level arus ekspektasi per jam berdasarkan pola Unibang"""
    level_map = {
        1: 32, 2: 32, 3: 32, 4: 32, 5: 32, 6: 35,
        7: 39, 8: 42, 9: 45, 10: 55,
        11: 64, 12: 65, 13: 64, 14: 65, 15: 64,
        16: 60, 17: 55, 18: 50,
        19: 45, 20: 42, 21: 39, 22: 37,
        23: 35, 0: 33
    }
    return level_map.get(hour, 40)


def create_unibang_features(datetime_index, historical_data=None):
    """Bangun fitur eksogen feeder Unibang"""
    df_feat = pd.DataFrame(index=datetime_index)
    df_feat["hour"] = datetime_index.hour
    df_feat["dayofweek"] = datetime_index.dayofweek

    df_feat["is_weekend"] = (df_feat["dayofweek"] >= 5).astype(int)
    df_feat["night_constant"] = df_feat["hour"].between(1, 6).astype(int)
    df_feat["peak_constant"] = df_feat["hour"].between(11, 15).astype(int)
    df_feat["evening_decline"] = df_feat["hour"].between(19, 22).astype(int)
    df_feat["morning_rise"] = df_feat["hour"].between(6, 10).astype(int)
    df_feat["hour_sin"] = np.sin(2 * np.pi * df_feat["hour"] / 24)
    df_feat["hour_cos"] = np.cos(2 * np.pi * df_feat["hour"] / 24)
    df_feat["expected_level"] = df_feat["hour"].apply(get_expected_level)

    # Tambahkan lag dan stabilitas jika tersedia data historis
    if historical_data is not None and len(historical_data) > 24:
        df_feat["lag_1"] = historical_data.shift(1).reindex(datetime_index, method="nearest")
        df_feat["lag_24"] = historical_data.shift(24).reindex(datetime_index, method="nearest")
        rolling_std = historical_data.rolling(6).std()
        global_std = historical_data.std()
        df_feat["stability"] = (rolling_std < global_std * 0.5).astype(int).reindex(datetime_index, method="nearest")
    else:
        df_feat["lag_1"] = 0
        df_feat["lag_24"] = 0
        df_feat["stability"] = 1

    return df_feat.fillna(0)


def prepare_exog(future_index, historical_data=None):
    """Siapkan variabel eksogen sesuai model Unibang"""
    exog_vars = [
        "hour_sin", "hour_cos", "is_weekend",
        "night_constant", "peak_constant",
        "evening_decline", "morning_rise",
        "lag_1", "lag_24", "stability", "expected_level"
    ]
    features = create_unibang_features(future_index, historical_data)
    return features[exog_vars]


def forecast(df_historical, steps=72, start_datetime=None):
    """
    Forecast arus 72 jam ke depan untuk feeder Unibang.
    df_historical: DataFrame dengan kolom 'arus' dan index datetime
    """
    model = load_model()

    if start_datetime is None:
        start_datetime = df_historical.index.max() + pd.Timedelta(hours=1)

    future_index = pd.date_range(start=start_datetime, periods=steps, freq="H")

    try:
        exog = prepare_exog(future_index, df_historical["arus"])
        forecast_values = model.forecast(steps=steps, exog=exog)
    except Exception as e:
        print(f"Warning: Forecast dengan exog gagal ({e}), mencoba tanpa exog.")
        forecast_values = model.forecast(steps=steps)

    forecast_df = pd.DataFrame({
        "datetime": future_index,
        "forecast": np.round(forecast_values, 2)
    })

    return forecast_df