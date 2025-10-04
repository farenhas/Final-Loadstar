import pandas as pd
import numpy as np
import pickle
from pathlib import Path

MODEL_PATH = Path("models/model_labang.pkl")

def load_model():
    """Load model pickle feeder Labang"""
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model

def get_time_period_labang(hour):
    if 6 <= hour <= 11:
        return 'pagi'
    elif 12 <= hour <= 17:
        return 'siang'
    elif 18 <= hour <= 21:
        return 'sore'
    else:
        return 'malam'

def prepare_exog(df):
    """Bangun fitur eksogen feeder Labang sesuai pola harian & mingguan"""
    df_exog = pd.DataFrame(index=df.index)
    df_exog['hour'] = df.index.hour
    df_exog['weekday'] = df.index.weekday
    df_exog['time_period'] = df.index.hour.map(get_time_period_labang)

    df_exog['senin_pagi_sore'] = ((df_exog['weekday'] == 0) &
                                  (df_exog['time_period'].isin(['pagi','siang','sore']))).astype(int) * 3
    df_exog['selasa_sore'] = ((df_exog['weekday'] == 1) &
                              (df_exog['time_period'] == 'sore')).astype(int) * 2
    df_exog['selasa_malam_anomali'] = ((df_exog['weekday'] == 1) &
                                       (df_exog['time_period'] == 'malam')).astype(int) * -5
    df_exog['rabu_recovery'] = ((df_exog['weekday'] == 2) &
                                (df_exog['time_period'].isin(['pagi','siang','sore']))).astype(int) * 4
    df_exog['minggu_siang_drop'] = ((df_exog['weekday'] == 6) &
                                    (df_exog['time_period'] == 'siang')).astype(int) * -2

    df_exog['is_peak_sore'] = (df_exog['time_period'] == 'sore').astype(int) * 4
    df_exog['is_malam_medium'] = (df_exog['time_period'] == 'malam').astype(int) * 2
    df_exog = df_exog.fillna(0)

    if 'arus' in df.columns:
        df_exog['roll_med_24'] = df['arus'].rolling(24, min_periods=1).median()
        df_exog['ratio_to_med'] = df['arus'] / df_exog['roll_med_24'].replace(0, np.nan)
        df_exog['is_anomaly_high'] = (df_exog['ratio_to_med'] > 1.3).astype(int) * 2
        df_exog['is_anomaly_low'] = (df_exog['ratio_to_med'] < 0.7).astype(int) * -2
    else:
        df_exog['is_anomaly_high'] = 0
        df_exog['is_anomaly_low'] = 0

    exog_cols = [
        'is_peak_sore',
        'senin_pagi_sore',
        'selasa_sore',
        'selasa_malam_anomali',
        'rabu_recovery',
        'minggu_siang_drop',
        'is_malam_medium',
        'is_anomaly_low',
        'is_anomaly_high'
    ]
    return df_exog[exog_cols]

def forecast(df_historical, steps=72, start_datetime=None):
    """Forecast 72 jam ke depan untuk feeder Labang"""
    model = load_model()

    df = df_historical.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime')

    df['arus'] = df['arus'].fillna(method='ffill').fillna(method='bfill')
    upper = df['arus'].quantile(0.985)
    lower = df['arus'].quantile(0.015)
    df['arus'] = df['arus'].clip(lower=lower, upper=upper)

    if start_datetime is None:
        start_datetime = df.index.max() + pd.Timedelta(hours=1)

    future_index = pd.date_range(start=start_datetime, periods=steps, freq='H')
    exog_future = prepare_exog(pd.DataFrame(index=future_index))

    forecast_values = model.forecast(steps=steps, exog=exog_future)
    forecast_values = np.maximum(forecast_values, 0)

    forecast_df = pd.DataFrame({
        'datetime': future_index,
        'forecast': forecast_values
    })
    return forecast_df
