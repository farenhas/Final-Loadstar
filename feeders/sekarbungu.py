import pandas as pd
import numpy as np
import pickle
import os

MODEL_PATH = "models/model_sekarbungu.pkl"
FORECAST_HORIZON = 72
HISTORY_LENGTH = 1440

def load_model():
    """Load model pickle feeder Birem"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model
    
def prepare_exog(index):
    df = pd.DataFrame(index=index)
    df["hour"] = df.index.hour
    df['stagnant_morning'] = df['hour'].apply(lambda x: 1 if 7 <= x <= 9 else 0)
    df['stagnant_afternoon'] = df['hour'].apply(lambda x: 1 if 12 <= x <= 16 else 0)
    df['stagnant_night'] = df['hour'].apply(lambda x: 1 if 1 <= x <= 3 else 0)
    df['stagnant_evening'] = df['hour'].apply(lambda x: 1 if 18 <= x <= 20 else 0)

    return df[['stagnant_morning', 'stagnant_afternoon',
           'stagnant_night', 'stagnant_evening']]

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
