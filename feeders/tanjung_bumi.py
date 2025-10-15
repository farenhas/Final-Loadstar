import pandas as pd
import numpy as np
import pickle
import os

MODEL_PATH = "models/model_TanjungBumi.pkl"

def load_model():
    """Load model pickle feeder Tanjung Bumi"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        package = pickle.load(f)
    return package


def create_features(timestamp, y_rolling, last_trend, trend_change_rate, seasonal_hist, hourly_expected, step_i):
    """Generate single timestep features untuk Tanjung Bumi"""
    hour = timestamp.hour
    dow = timestamp.dayofweek
    
    feat = {}
    
    # Time features (cyclic encoding)
    feat['hour_sin'] = np.sin(2*np.pi*hour/24)
    feat['hour_cos'] = np.cos(2*np.pi*hour/24)
    feat['dow_sin'] = np.sin(2*np.pi*dow/7)
    feat['dow_cos'] = np.cos(2*np.pi*dow/7)
    
    # Period indicators
    feat['is_weekend'] = int(dow >= 5)
    feat['dini_hari'] = int(0 <= hour <= 5)
    feat['pagi'] = int(6 <= hour <= 11)
    feat['siang'] = int(12 <= hour <= 16)
    feat['sore_puncak'] = int(17 <= hour <= 19)
    feat['malam'] = int(20 <= hour <= 23)
    
    # Lag features
    feat['lag_1'] = y_rolling.iloc[-1]
    feat['lag_24'] = y_rolling.iloc[-24] if len(y_rolling) >= 24 else y_rolling.mean()
    feat['lag_168'] = y_rolling.iloc[-168] if len(y_rolling) >= 168 else y_rolling.mean()
    
    # Rolling statistics
    feat['rolling_mean_3h'] = y_rolling.tail(3).mean()
    feat['rolling_mean_6h'] = y_rolling.tail(6).mean()
    feat['rolling_mean_24h'] = y_rolling.tail(24).mean()
    feat['rolling_std_6h'] = y_rolling.tail(6).std()
    feat['rolling_std_24h'] = y_rolling.tail(24).std()
    
    # Volatility indicator
    feat['is_volatile'] = int(feat['rolling_std_6h'] > y_rolling.std() * 0.5)
    
    # Expected pattern
    feat['expected'] = hourly_expected.get(hour, 150)
    feat['deviation_from_expected'] = (y_rolling.iloc[-1] - feat['expected']) / (feat['expected'] + 1)
    
    # Interaction features
    feat['weekend_peak'] = feat['is_weekend'] * feat['sore_puncak']
    feat['volatile_peak'] = feat['is_volatile'] * feat['sore_puncak']
    feat['weekend_night'] = feat['is_weekend'] * feat['malam']
    
    # Trend & seasonal
    projected_trend = last_trend + (trend_change_rate * (step_i + 1))
    feat['trend'] = projected_trend
    feat['seasonal'] = seasonal_hist.iloc[step_i % len(seasonal_hist)]
    feat['trend_change'] = trend_change_rate
    
    return feat


def apply_constraints(pred_raw, hour, hourly_expected):
    """Apply post-processing constraints"""
    expected = hourly_expected.get(hour, 150)
    lower_bound = expected * 0.6
    upper_bound = expected * 1.4
    
    pred = np.clip(pred_raw, lower_bound, upper_bound)
    pred = np.clip(pred, 50, 300)
    
    return pred


def forecast(df_historical, steps=72, start_datetime=None):
    """
    Forecast arus 72 jam ke depan untuk feeder Tanjung Bumi.
    
    Parameters:
    -----------
    df_historical : DataFrame
        DataFrame dengan kolom 'arus' dan index datetime
    steps : int
        Jumlah jam yang akan diforecast (default 72)
    start_datetime : datetime
        Waktu mulai forecast (default: 1 jam setelah data terakhir)
    
    Returns:
    --------
    DataFrame dengan kolom 'datetime' dan 'forecast'
    """
    from statsmodels.tsa.seasonal import seasonal_decompose
    
    # Load model package
    package = load_model()
    model = package['model']
    exog_cols = package['exog_cols']
    hourly_expected = package['hourly_expected']
    
    # Ensure index is datetime
    if not isinstance(df_historical.index, pd.DatetimeIndex):
        df_historical.index = pd.to_datetime(df_historical.index)
    
    # Prepare historical data (last 1440 hours = 60 days)
    y_hist = df_historical['arus'].tail(1440).copy()
    
    # Seasonal decomposition
    decomp = seasonal_decompose(y_hist, model='additive', period=24, extrapolate_trend='freq')
    trend_hist = decomp.trend
    seasonal_hist = decomp.seasonal
    
    last_trend = trend_hist.iloc[-1]
    trend_change_rate = trend_hist.diff().tail(24).mean()
    
    # Determine forecast start
    if start_datetime is None:
        start_datetime = y_hist.index[-1] + pd.Timedelta(hours=1)
    
    # Generate future index
    future_index = pd.date_range(start=start_datetime, periods=steps, freq='H')
    
    # Iterative forecasting
    forecast_values = []
    y_rolling = y_hist.copy()
    
    for i, timestamp in enumerate(future_index):
        # Create features for this timestep
        feat = create_features(
            timestamp, 
            y_rolling, 
            last_trend, 
            trend_change_rate, 
            seasonal_hist, 
            hourly_expected, 
            i
        )
        
        # Create exog dataframe
        exog_df = pd.DataFrame([feat], columns=exog_cols)
        
        # Forecast single step
        pred_raw = model.forecast(steps=1, exog=exog_df).values[0]
        
        # Apply constraints
        pred = apply_constraints(pred_raw, timestamp.hour, hourly_expected)
        
        forecast_values.append(pred)
        
        # Update rolling window
        y_rolling = pd.concat([y_rolling, pd.Series([pred], index=[timestamp])])
    
    # Create forecast dataframe
    forecast_df = pd.DataFrame({
        'datetime': future_index,
        'forecast': np.round(forecast_values, 2)
    })
    
    return forecast_df