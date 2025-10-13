import pandas as pd
import numpy as np
import pickle
import os
from pathlib import Path

MODEL_PATH = Path(__file__).parent.parent / "models" / "model_Galis.pkl"

def load_model():
    """Load model pickle feeder Galis"""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    
    with open(MODEL_PATH, "rb") as f:
        data = pickle.load(f)
    
    return data


def create_galis_features(datetime_index, historical_data=None):
    """Generate exogenous features untuk feeder Galis"""
    df = pd.DataFrame(index=datetime_index)
    
    hours = datetime_index.hour.values
    days = datetime_index.dayofweek.values
    
    # Cyclic time features
    df['sin_hour'] = np.sin(2 * np.pi * hours / 24)
    df['cos_hour'] = np.cos(2 * np.pi * hours / 24)
    df['sin_day'] = np.sin(2 * np.pi * days / 7)
    df['cos_day'] = np.cos(2 * np.pi * days / 7)
    
    # Weekend indicator
    df['is_weekend'] = (days >= 5).astype(np.int8)
    
    # Peak hours (17-18)
    df['is_peak'] = np.isin(hours, [17, 18]).astype(np.int8)
    
    # High load hours (16-19)
    df['is_high'] = np.isin(hours, [16, 17, 18, 19]).astype(np.int8)
    
    # Post-peak hours (19-21)
    df['is_post'] = np.isin(hours, [19, 20, 21]).astype(np.int8)
    
    # Morning hours (6-9)
    df['is_morning'] = np.isin(hours, [6, 7, 8, 9]).astype(np.int8)
    
    # Night hours (0-5)
    df['is_night'] = np.isin(hours, [0, 1, 2, 3, 4, 5]).astype(np.int8)
    
    # Historical patterns dari model (fallback values)
    galis_hourly = {
        0:130, 1:122, 2:119, 3:117, 4:115, 5:116, 6:118, 7:95, 8:96, 9:99, 
        10:102, 11:104, 12:101, 13:98, 14:96, 15:98, 16:107, 17:156, 18:164, 
        19:154, 20:147, 21:141, 22:138, 23:134
    }
    
    df['hist_med'] = pd.Series(hours).map(lambda h: galis_hourly.get(h, 115)).values
    df['hist_std'] = 8.0  # Default std
    
    # Lag features - gunakan historical data jika tersedia
    if historical_data is not None and len(historical_data) > 48:
        last_values = historical_data.tail(48).values
        df['lag_1'] = last_values[-1] if len(last_values) >= 1 else 115
        df['lag_2'] = last_values[-2] if len(last_values) >= 2 else 115
        df['lag_24'] = last_values[-24] if len(last_values) >= 24 else 115
        df['lag_48'] = last_values[-48] if len(last_values) >= 48 else 115
        
        # Rolling means
        df['roll_3'] = np.mean(last_values[-3:]) if len(last_values) >= 3 else 115
        df['roll_6'] = np.mean(last_values[-6:]) if len(last_values) >= 6 else 115
        df['roll_24'] = np.mean(last_values[-24:]) if len(last_values) >= 24 else 115
        
        # Differences
        df['diff_1'] = last_values[-1] - last_values[-2] if len(last_values) >= 2 else 0
        df['diff_24'] = last_values[-1] - last_values[-24] if len(last_values) >= 24 else 0
    else:
        # Default values jika tidak ada historical data
        df['lag_1'] = 115
        df['lag_2'] = 115
        df['lag_24'] = 115
        df['lag_48'] = 115
        df['roll_3'] = 115
        df['roll_6'] = 115
        df['roll_24'] = 115
        df['diff_1'] = 0
        df['diff_24'] = 0
    
    # Expected value (sama dengan hist_med untuk simplicity)
    df['expected'] = df['hist_med']
    
    return df


def prepare_exog(future_index, historical_data=None):
    """Siapkan exogenous variables sesuai urutan yang digunakan model Galis"""
    exog_vars = [
        'is_weekend', 'sin_hour', 'cos_hour', 'sin_day', 'cos_day',
        'is_peak', 'is_high', 'is_post', 'is_morning', 'is_night',
        'hist_med', 'hist_std', 'lag_1', 'lag_2', 'lag_24', 'lag_48',
        'roll_3', 'roll_6', 'roll_24', 'diff_1', 'diff_24', 'expected'
    ]
    
    features = create_galis_features(future_index, historical_data)
    return features[exog_vars].fillna(0)


def apply_galis_patterns(base_forecast, datetime_index, model_data):
    """Terapkan pola historis Galis untuk memperbaiki prediksi"""
    hours = datetime_index.hour.values
    is_weekend = datetime_index.dayofweek.values >= 5
    
    # Load patterns dari model
    hourly_patterns = model_data.get('patterns', {})
    weekday_patterns = model_data.get('weekday', {})
    weekend_patterns = model_data.get('weekend', {})
    config = model_data.get('config', ((1,0,1), (1,0,1,24), 0.35, 0.45))
    
    peak_weight = config[2] if len(config) > 2 else 0.35
    post_weight = config[3] if len(config) > 3 else 0.45
    
    # Buat pattern array
    pattern = np.zeros(len(datetime_index))
    for i, (h, we) in enumerate(zip(hours, is_weekend)):
        if we and h in weekend_patterns:
            pattern[i] = weekend_patterns[h]
        elif not we and h in weekday_patterns:
            pattern[i] = weekday_patterns[h]
        elif h in hourly_patterns:
            pattern[i] = hourly_patterns[h].get('median', 115)
        else:
            pattern[i] = 115
    
    # Weighted ensemble
    w_sar = np.where(
        np.isin(hours, [17, 18]), 1 - peak_weight,
        np.where(
            np.isin(hours, [19, 20, 21]), 1 - post_weight,
            np.where(np.isin(hours, [6, 7, 8, 9]), 0.40, 0.45)
        )
    )
    
    ensemble = w_sar * base_forecast + (1 - w_sar) * pattern
    
    # Trend smoothing (antar hari)
    for i in range(24, len(ensemble)):
        ensemble[i] = 0.92 * ensemble[i] + 0.08 * ensemble[i-24]
    
    # Apply bounds berdasarkan jam
    lower = np.array([hourly_patterns.get(h, {}).get('min', 80) for h in hours])
    upper = np.array([hourly_patterns.get(h, {}).get('max', 180) for h in hours])
    
    # Peak hours bounds
    peak_mask = np.isin(hours, [17, 18])
    lower[peak_mask] = 150
    upper[peak_mask] = 170
    
    # Post-peak bounds
    post_mask = np.isin(hours, [19, 20])
    lower[post_mask] = 140
    upper[post_mask] = 165
    
    # Morning/night bounds
    morning_mask = np.isin(hours, [0, 1, 2, 3, 4, 5, 6])
    lower[morning_mask] = 95
    upper[morning_mask] = 130
    
    # Clip to bounds
    result = np.clip(ensemble, lower, upper)
    
    return result


def forecast(df_historical, steps=72, start_datetime=None):
    """
    Forecast arus 72 jam ke depan untuk feeder Galis.
    
    Parameters:
    -----------
    df_historical : DataFrame
        DataFrame dengan index datetime dan kolom 'arus'
    steps : int
        Jumlah jam forecast (default 72)
    start_datetime : datetime
        Waktu mulai forecast (default: 1 jam setelah data terakhir)
    
    Returns:
    --------
    DataFrame dengan kolom ['datetime', 'forecast']
    """
    
    # Load model
    try:
        model_data = load_model()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None
    
    # Extract model dan fitted object
    if isinstance(model_data, dict):
        fitted_model = model_data.get('model')
        if fitted_model is None:
            print("Error: Model object tidak ditemukan dalam pickle")
            return None
    else:
        fitted_model = model_data
        model_data = {'model': fitted_model, 'patterns': {}, 'weekday': {}, 'weekend': {}}
    
    # Pastikan df_historical memiliki index datetime
    if not isinstance(df_historical.index, pd.DatetimeIndex):
        if 'timestamp' in df_historical.columns:
            df_historical = df_historical.set_index('timestamp')
        else:
            print("Error: DataFrame harus memiliki datetime index")
            return None
    
    # Set start datetime
    if start_datetime is None:
        start_datetime = df_historical.index.max() + pd.Timedelta(hours=1)
    
    # Buat future index
    future_index = pd.date_range(start=start_datetime, periods=steps, freq='H')
    
    # Prepare exogenous variables
    try:
        historical_series = df_historical['arus'] if 'arus' in df_historical.columns else df_historical.iloc[:, 0]
        exog = prepare_exog(future_index, historical_series)
        
        # Forecast dengan model SARIMAX
        base_forecast = fitted_model.forecast(steps=steps, exog=exog)
        
        # Apply Galis-specific patterns
        final_forecast = apply_galis_patterns(base_forecast.values, future_index, model_data)
        
    except Exception as e:
        print(f"Warning: Forecast dengan exog gagal ({e}), menggunakan pattern-based forecast...")
        
        # Fallback: gunakan pattern saja
        hourly_patterns = model_data.get('patterns', {})
        weekday_patterns = model_data.get('weekday', {})
        weekend_patterns = model_data.get('weekend', {})
        
        hours = future_index.hour.values
        is_weekend = future_index.dayofweek.values >= 5
        
        final_forecast = np.zeros(steps)
        for i, (h, we) in enumerate(zip(hours, is_weekend)):
            if we and h in weekend_patterns:
                final_forecast[i] = weekend_patterns[h]
            elif not we and h in weekday_patterns:
                final_forecast[i] = weekday_patterns[h]
            elif h in hourly_patterns:
                final_forecast[i] = hourly_patterns[h].get('median', 115)
            else:
                # Default pattern
                default_pattern = {
                    0:130, 1:122, 2:119, 3:117, 4:115, 5:116, 6:118, 7:95, 8:96, 9:99,
                    10:102, 11:104, 12:101, 13:98, 14:96, 15:98, 16:107, 17:156, 18:164,
                    19:154, 20:147, 21:141, 22:138, 23:134
                }
                final_forecast[i] = default_pattern.get(h, 115)
    
    # Buat output DataFrame
    forecast_df = pd.DataFrame({
        'datetime': future_index,
        'forecast': np.round(final_forecast, 2)
    })
    
    return forecast_df


# Untuk testing
if __name__ == "__main__":
    print("Testing Galis Forecast Module...")
    print(f"Model path: {MODEL_PATH}")
    print(f"Model exists: {MODEL_PATH.exists()}")
    
    # Create dummy historical data untuk testing
    dates = pd.date_range(end=pd.Timestamp.now(), periods=168, freq='H')
    dummy_data = pd.DataFrame({
        'arus': np.random.uniform(90, 160, 168)
    }, index=dates)
    
    try:
        result = forecast(dummy_data, steps=72)
        if result is not None:
            print("\nForecast berhasil!")
            print(f"Shape: {result.shape}")
            print("\nSample data:")
            print(result.head(10))
            print("\nStatistik:")
            print(result['forecast'].describe())
        else:
            print("\nForecast gagal - returned None")
    except Exception as e:
        print(f"\nError saat testing: {e}")
        import traceback
        traceback.print_exc()