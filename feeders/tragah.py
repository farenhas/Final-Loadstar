import pandas as pd
import pickle
import numpy as np

MODEL_PATH = "models/model_Tragah.pkl"

def load_model():
    """Load model pkl Tragah"""
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model

def prepare_exog(future_index):
    """Buat exogenous variables untuk forecast sesuai model"""
    df_exog = pd.DataFrame(index=future_index)
    df_exog['hour'] = df_exog.index.hour
    df_exog['dayofweek'] = df_exog.index.dayofweek
    df_exog['is_weekend'] = (df_exog['dayofweek'] >= 5).astype(int)
    df_exog['is_midnight'] = df_exog['hour'].between(0,4).astype(int)
    df_exog['is_morning_drop'] = df_exog['hour'].between(5,8).astype(int)
    # Hanya kolom yang digunakan model
    return df_exog[['is_weekend','is_midnight','is_morning_drop']]

def forecast(df_historical, steps=72, start_datetime=None):
    """
    df_historical: DataFrame historis (index datetime)
    steps: jumlah jam ke depan
    start_datetime: datetime mulai forecast (default: last historical datetime + 1 jam)
    """
    model = load_model()
    
    if start_datetime is None:
        start_datetime = df_historical.index.max() + pd.Timedelta(hours=1)
    
    future_index = pd.date_range(start=start_datetime, periods=steps, freq='H')
    exog = prepare_exog(future_index)
    
    forecast_values = model.forecast(steps=steps, exog=exog)
    forecast_df = pd.DataFrame({'datetime': future_index, 'forecast': forecast_values})
    return forecast_df
