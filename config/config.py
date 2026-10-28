import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hydro-vision-dev-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///hydrovision.db')
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True} if SQLALCHEMY_DATABASE_URI.startswith('postgresql') else {}
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    DATA_RAW = os.path.join(BASE_DIR, 'data', 'raw')
    DATA_PROCESSED = os.path.join(BASE_DIR, 'data', 'processed')
    DATA_FEATURES = os.path.join(BASE_DIR, 'data', 'features')
    MODEL_PATH = os.path.join(BASE_DIR, 'models')
    REPORT_PATH = os.path.join(BASE_DIR, 'reports')
    GIS_CONFIG_PATH = os.path.join(BASE_DIR, 'gis', 'config.json')
    RISK_THRESHOLDS_PATH = os.path.join(BASE_DIR, 'config', 'risk_thresholds.json')
    PRIMARY_MODEL = 'xgboost'
    RANDOM_STATE = 42
