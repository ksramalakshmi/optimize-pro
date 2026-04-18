import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'optimize-pro-dev-secret-key-change-in-prod')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'optimize_pro.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    }
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max upload

    # ML Configuration
    FORECAST_HORIZON = 14  # days
    MIN_DATA_SMA = 7
    MIN_DATA_EXP_SMOOTH = 14
    MIN_DATA_HOLT_WINTERS = 30
    SAFETY_FACTOR = 1.5
    DEFAULT_LEAD_TIME = 7  # days

    # Cache TTL (seconds)
    CACHE_TTL_ANALYTICS = 300  # 5 minutes
    CACHE_TTL_FORECASTS = 86400  # 24 hours
    CACHE_TTL_ALERTS = 60  # 1 minute

    # Alert Thresholds
    CRITICAL_DAYS = 3
    HIGH_ALERT_DAYS = 7
    OVERSTOCK_MULTIPLIER = 2  # 2x forecast horizon = overstock

    # Allocation
    MIN_ALLOCATION_PER_MARKETPLACE = 5

    # Currency
    CURRENCY_SYMBOL = '₹'
