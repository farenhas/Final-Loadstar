import pandas as pd
import numpy as np
import pickle
import os

MODEL_PATH = "models/model_birem.pkl"

def load_model():
    """Load model pickle feeder Birem"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model


def get_time_period(hour):
    """Klasifikasi jam ke dalam periode waktu"""
    if 6 <= hour <= 11:
        return 'pagi'
    elif 12 <= hour <= 17:
        return 'siang'
    elif 18 <= hour <= 21:
        return 'sore'
    else:
        return 'malam'


def create_birem_features(datetime_index, historical_data=None):
    """Generate exogenous features khusus feeder Birem"""
    df_feat = pd.DataFrame(index=datetime_index)

    # Time-based features
    df_feat['time_period'] = datetime_index.hour.map(get_time_period)
    df_feat['weekday'] = datetime_index.weekday

    # Pola spesifik Birem (dari notebook)
    df_feat['kamis_pagi_malam'] = ((df_feat['weekday'] == 3) &
                                  (df_feat['time_period'].isin(['pagi', 'malam']))).astype(int) * 2
    df_feat['jumat_pagi_malam'] = ((df_feat['weekday'] == 4) &
                                  (df_feat['time_period'].isin(['pagi', 'siang', 'sore', 'malam']))).astype(int) * 3
    df_feat['minggu_pagi_malam'] = ((df_feat['weekday'] == 6) &
                                   (df_feat['time_period'].isin(['pagi', 'malam']))).astype(int) * 2
    df_feat['senin_pagi_sore'] = ((df_feat['weekday'] == 0) &
                                 (df_feat['time_period'].isin(['pagi', 'siang', 'sore']))).astype(int) * 4
    df_feat['rabu_malam'] = ((df_feat['weekday'] == 2) &
                            (df_feat['time_period'] == 'malam')).astype(int)
    df_feat['sabtu_pagi_malam'] = ((df_feat['weekday'] == 5) &
                                  (df_feat['time_period'].isin(['pagi', 'malam']))).astype(int)
    df_feat['selasa_pagi_sore'] = ((df_feat['weekday'] == 1) &
                                  (df_feat['time_period'].isin(['pagi', 'siang', 'sore']))).astype(int) * 3

    df_feat['is_peak_sore'] = (df_feat['time_period'] == 'sore').astype(int)
    df_feat['is_low_pagi'] = (df_feat['time_period'] == 'pagi').astype(int)

    # Drop probability detection (based on last 7 days)
    if historical_data is not None and len(historical_data) > 24:
        recent_data = historical_data.tail(168)
        roll_med = recent_data.rolling(24, min_periods=1).median().iloc[-1]
        recent_drop_rate = ((recent_data / roll_med) < 0.6).mean()
    else:
        recent_drop_rate = 0.05

    np.random.seed(42)
    base_drop_prob = np.where(
        (datetime_index.hour >= 22) | (datetime_index.hour <= 5),
        recent_drop_rate * 2,
        recent_drop_rate
    )
    df_feat['is_drop_now'] = (np.random.random(len(datetime_index)) < base_drop_prob).astype(int)

    return df_feat


def prepare_exog(future_index, historical_data=None):
    """Siapkan exogenous variables sesuai kolom yang digunakan model Birem"""
    exog_vars = [
        'kamis_pagi_malam', 'jumat_pagi_malam', 'minggu_pagi_malam',
        'senin_pagi_sore', 'rabu_malam', 'sabtu_pagi_malam',
        'selasa_pagi_sore', 'is_peak_sore', 'is_low_pagi', 'is_drop_now'
    ]
    features = create_birem_features(future_index, historical_data)
    return features[exog_vars].fillna(0)


def forecast(df_historical, steps=72, start_datetime=None):
    """
    Forecast arus 72 jam ke depan untuk feeder Birem.
    df_historical: DataFrame dengan kolom 'arus' dan index datetime
    """
    model = load_model()

    if start_datetime is None:
        start_datetime = df_historical.index.max() + pd.Timedelta(hours=1)

    # Buat future index
    future_index = pd.date_range(start=start_datetime, periods=steps, freq='H')

    try:
        exog = prepare_exog(future_index, df_historical['arus'])
        forecast_values = model.forecast(steps=steps, exog=exog)
    except Exception as e:
        print(f"Warning: Forecast dengan exog gagal ({e}), mencoba tanpa exog.")
        forecast_values = model.forecast(steps=steps)

    forecast_df = pd.DataFrame({
        'datetime': future_index,
        'forecast': np.round(forecast_values, 2)
    })

    return forecast_df
