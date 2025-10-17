"""
Business Logic Constants for Load Forecaster Dashboard
Thresholds, feeder relationships, and configuration values
"""

from pathlib import Path

# ============================================================
# FORECASTING PARAMETERS
# ============================================================

FORECAST_HOURS = 72          # Forecast duration in hours
HIST_DAYS = 7               # Historical data display window (days)

# ============================================================
# ELECTRICAL THRESHOLDS
# ============================================================

MAX_CAPACITY = 400.0        # Maximum feeder capacity (Amperes)
WARNING_THRESHOLD = 320.0   # Warning threshold (80% of capacity)
SAFE_THRESHOLD = 256.0      # Safe threshold (64% of capacity)

# Threshold percentages
WARNING_PCT = 0.80          # 80% capacity
SAFE_PCT = 0.64             # 64% capacity

# ============================================================
# FEEDER RELATIONSHIPS
# ============================================================
# Mapping of source feeders to their possible transfer partners

FEEDER_PAIRS = {
    "aros baya": ["pemuda kaffa", "tanjung bumi", "gegger"],
    "suramadu": ["pemuda kaffa", "parseh"],
    "labang": ["sekarbungu", "tragah", "galis", "alas kembang"],
    "tragah": ["tanah merah", "labang", "alang-alang"],
    "alang-alang": ["tragah"],
    "parseh": ["suramadu", "unibang"],
    "tanah merah": ["tragah", "alas kembang", "tanjung bumi", "torjun"],
    "tanjung bumi": ["tanah merah", "birem", "alas kembang"],
    "alas kembang": ["tragah", "tanah merah", "gegger"],
    "gegger": ["aros baya", "alas kembang"],
    "pemuda kaffa": ["suramadu"],
    "galis": ["labang", "torjun"],
    "birem": ["tanjung bumi"],
    "torjun": ["tanah merah", "galis"],
    "unibang": ["parseh"],
    "sekarbungu": ["labang"],
}

# Normalize all feeder names to lowercase for consistency
FEEDER_PAIRS = {k.lower(): [t.lower() for t in v] for k, v in FEEDER_PAIRS.items()}

# ============================================================
# FEEDER MODULE MAPPING
# ============================================================
# Map feeder names to their forecast modules

FEEDER_MODULES = {
    "birem": "birem",
    "gegger": "gegger",
    "labang": "labang",
    "tragah": "tragah",
    "torjun": "torjun",
    "galis": "galis",
    "unibang": "unibang",
    "alas kembang": "alas_kembang",
    "alang-alang": "alang_alang",
    "pemuda kaffa": "pemuda_kaffa",
    "aros baya": "aros_baya",
    "sekarbungu": "sekarbungu",
    "tanah merah": "tanah_merah",
    "suramadu": "suramadu",
    "tanjung bumi": "tanjung_bumi",
    "parseh": "parseh",
}

# ============================================================
# FILE PATHS
# ============================================================

# Logo path (adjust based on your directory structure)
LOGO_PATH = Path(r"D:\Magang\ForecastArus\loadstar.png")

# Alternative paths for different environments
LOGO_PATH_ALTERNATIVES = [
    Path("loadstar.png"),
    Path("assets/loadstar.png"),
    Path("static/loadstar.png"),
]

# ============================================================
# TIME CONFIGURATION
# ============================================================

# Hour options for time picker (24-hour format)
HOUR_OPTIONS = list(range(24))  # 0-23

# Default time range
DEFAULT_START_HOUR = 0   # 00:00
DEFAULT_END_HOUR = 23    # 23:00

# ============================================================
# CHART CONFIGURATION
# ============================================================

# Chart colors for different data types
CHART_COLORS = {
    'forecast': '#5b6fa8',      # Primary blue for forecasts
    'partner': '#6366f1',       # Indigo for partner feeders
    'total': '#10b981',         # Green for total (safe)
    'warning': '#f59e0b',       # Orange for warnings
    'danger': '#ef4444',        # Red for danger
    'realtime': '#3b82f6',      # Sky blue for real-time data
}

# Chart dimensions
CHART_HEIGHT = {
    'small': 280,
    'medium': 320,
    'large': 400,
}

# ============================================================
# DATA COLUMN NAMES
# ============================================================

# Standard column names for data processing
COLUMN_NAMES = {
    'timestamp': 'timestamp',
    'datetime': 'datetime',
    'forecast': 'forecast',
    'arus': 'arus',
    'feeder': 'feeder_name',
}

# Alternative column names that might appear in data
COLUMN_ALIASES = {
    'timestamp': ['timestamp', 'datetime', 'ds', 'date', 'time'],
    'forecast': ['forecast', 'prediction', 'pred', 'yhat', 'value'],
    'arus': ['arus', 'current', 'ampere', 'load'],
}

# ============================================================
# UI TEXT LABELS
# ============================================================

LABELS = {
    'safe': 'Aman',
    'warning': 'Mendekati Batas',
    'danger': 'Tidak Aman',
    'no_data': 'Tidak ada data',
    'no_forecast': 'Model forecast belum tersedia',
    'no_partners': 'Tidak ada pasangan transfer',
    'loading': 'Memuat data...',
    'error': 'Terjadi kesalahan',
}

# Section titles
SECTION_TITLES = {
    'maneuver_forecast': 'Prediksi Feeder Manuver',
    'recommendations': 'Prediksi Beban Manuver',
    'forecast_72h': 'Prediksi Beban 72 Jam ke Depan',
    'detail_table': 'Rincian Prediksi Per Jam',
    'realtime': 'Beban Real-Time',
}

# ============================================================
# VALIDATION RULES
# ============================================================

# Maximum allowed forecast duration
MAX_FORECAST_DURATION_HOURS = 72

# Minimum historical data required for forecasting
MIN_HISTORICAL_HOURS = 24

# Data quality thresholds
MIN_DATA_POINTS = 10
MAX_MISSING_RATIO = 0.3  # Maximum 30% missing data

# ============================================================
# EXPORT CONFIGURATION
# ============================================================

# File formats for export
EXPORT_FORMATS = ['CSV', 'Excel', 'PDF']

# Default export filename template
EXPORT_FILENAME_TEMPLATE = "forecast_{feeder}_{date}.{ext}"

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_logo_path() -> Path:
    """
    Get the logo path, trying alternatives if primary path doesn't exist
    
    Returns:
        Path object to logo file, or None if not found
    """
    if LOGO_PATH.exists():
        return LOGO_PATH
    
    for alt_path in LOGO_PATH_ALTERNATIVES:
        if alt_path.exists():
            return alt_path
    
    return None


def get_feeder_partners(feeder_name: str) -> list:
    """
    Get list of partner feeders for a given feeder
    
    Args:
        feeder_name: Name of the feeder (case-insensitive)
        
    Returns:
        List of partner feeder names (lowercase)
    """
    return FEEDER_PAIRS.get(feeder_name.lower(), [])


def validate_load_value(value: float) -> tuple:
    """
    Validate load value and return status
    
    Args:
        value: Load value in Amperes
        
    Returns:
        Tuple of (is_valid, status, message)
    """
    if value < 0:
        return (False, 'error', 'Nilai beban tidak boleh negatif')
    elif value < WARNING_THRESHOLD:
        return (True, 'safe', 'Beban dalam kondisi aman')
    elif value < MAX_CAPACITY:
        return (True, 'warning', 'Beban mendekati batas maksimal')
    else:
        return (True, 'danger', 'Beban melebihi kapasitas maksimal')


def format_load_value(value: float, include_unit: bool = True) -> str:
    """
    Format load value for display
    
    Args:
        value: Load value in Amperes
        include_unit: Whether to include 'A' unit
        
    Returns:
        Formatted string
    """
    formatted = f"{value:.2f}"
    if include_unit:
        formatted += " A"
    return formatted