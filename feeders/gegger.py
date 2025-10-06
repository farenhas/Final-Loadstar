import pandas as pd
import numpy as np
import pickle
import os

MODEL_PATH = "models/model_gegger.pkl"

def load_model():
    """Load model pickle feeder Gegger"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model


def get_time_period(hour):
    """Klasifikasi jam ke dalam periode waktu (khusus Gegger)"""
    if 6 <= hour <= 11:
        return 'pagi'
    elif 12 <= hour <= 17:
        return 'siang'
    elif 18 <= hour <= 23:
        return 'sore_malam'
    else:
        return 'dini_hari'


def create_gegger_features(datetime_index, historical_data=None):
    """Generate exogenous features khusus feeder Gegger"""
    df_feat = pd.DataFrame(index=datetime_index)

    # Time-based features
    df_feat['time_period'] = datetime_index.hour.map(get_time_period)
    df_feat['weekday'] = datetime_index.weekday

    # Pola spesifik Gegger (dari analisis notebook)
    df_feat['sabtu_sore_malam'] = ((df_feat['weekday'] == 5) &
                                   (df_feat['time_period'] == 'sore_malam')).astype(int) * 2
    df_feat['kamis_siang_sore'] = ((df_feat['weekday'] == 3) &
                                   (df_feat['time_period'].isin(['siang', 'sore_malam']))).astype(int) * 3
    df_feat['minggu_siang'] = ((df_feat['weekday'] == 6) &
                               (df_feat['time_period'] == 'siang')).astype(int) * 2
    df_feat['selasa_pagi_sore'] = ((df_feat['weekday'] == 1) &
                                   (df_feat['time_period'].isin(['pagi', 'siang', 'sore_malam']))).astype(int) * 3
    df_feat['jumat_pagi_sore'] = ((df_feat['weekday'] == 4) &
                                  (df_feat['time_period'].isin(['pagi', 'siang', 'sore_malam']))).astype(int) * 4
    df_feat['rabu_pagi_sore'] = ((df_feat['weekday'] == 2) &
                                 (df_feat['time_period'].isin(['pagi', 'siang', 'sore_malam']))).astype(int) * 2

    # Pola umum
    df_feat['is_peak_sore_malam'] = (df_feat['time_period'] == 'sore_malam').astype(int)
    df_feat['is_low_dini_hari'] = (df_feat['time_period'] == 'dini_hari').astype(int)

    # Drop/spike detection berbasis historical_data
    if historical_data is not None and len(historical_data) > 48:
        roll_med_12 = historical_data.rolling(12, min_periods=1).median().iloc[-1]
        roll_std_24 = historical_data.rolling(24, min_periods=1).std().iloc[-1]
        recent_drop = (historical_data.iloc[-1] < 25)
        recent_spike = (historical_data.iloc[-1] > 85) and (historical_data.iloc[-2] < 30 if len(historical_data) > 1 else False)
    else:
        roll_med_12 = np.nan
        roll_std_24 = np.nan
        recent_drop = False
        recent_spike = False

    df_feat['is_extreme_drop'] = 1 if recent_drop else 0
    df_feat['is_recovery_spike'] = 1 if recent_spike else 0

    return df_feat


def prepare_exog(future_index, historical_data=None):
    """Siapkan exogenous variables sesuai kolom yang digunakan model Gegger"""
    exog_vars = [
        'sabtu_sore_malam', 'kamis_siang_sore', 'minggu_siang',
        'selasa_pagi_sore', 'jumat_pagi_sore', 'rabu_pagi_sore',
        'is_peak_sore_malam', 'is_low_dini_hari',
        'is_extreme_drop', 'is_recovery_spike'
    ]
    features = create_gegger_features(future_index, historical_data)
    return features[exog_vars].fillna(0)


def forecast(df_historical, steps=72, start_datetime=None):
    """
    Forecast arus 72 jam ke depan untuk feeder Gegger.
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
