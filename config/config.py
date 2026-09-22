import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hydro-vision-secret-key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///hydrovision.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Path configurations
    DATA_RAW = 'data/raw'
    DATA_PROCESSED = 'data/processed'
    DATA_FEATURES = 'data/features'
    MODEL_PATH = 'models'
    REPORT_PATH = 'reports'

    # ML Configuration
    PRIMARY_MODEL = 'xgboost'
    RANDOM_STATE = 42

    # GIS Configuration
    GIS_CONFIG_PATH = 'gis/config.json'
    RISK_THRESHOLDS_PATH = 'config/risk_thresholds.json'
