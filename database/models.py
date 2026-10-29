from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class WaterData(db.Model):
    """Stores historical and processed water resource data."""
    __tablename__ = 'water_data'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    evaporation = db.Column(db.Float)
    groundwater_level = db.Column(db.Float)
    reservoir_storage = db.Column(db.Float)
    population = db.Column(db.Float)
    water_demand = db.Column(db.Float)
    water_availability = db.Column(db.Float)
    # Provenance: synthetic_demo, mixed_synthetic_target, or legacy_demo.
    data_source = db.Column(db.String(40), nullable=False, default='legacy_demo')

class Prediction(db.Model):
    """Stores ML-generated predictions for future availability."""
    __tablename__ = 'predictions'
    id = db.Column(db.Integer, primary_key=True)
    prediction_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    predicted_availability = db.Column(db.Float)
    risk_level = db.Column(db.String(20))
    model_version = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Alert(db.Model):
    """Stores generated early warnings."""
    __tablename__ = 'alerts'
    id = db.Column(db.String(50), primary_key=True)
    location = db.Column(db.String(100))
    risk_level = db.Column(db.String(20))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='ACTIVE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ModelMetric(db.Model):
    """Stores performance metrics of trained models."""
    __tablename__ = 'model_metrics'
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(50))
    mae = db.Column(db.Float)
    mse = db.Column(db.Float)
    rmse = db.Column(db.Float)
    r2 = db.Column(db.Float)
    training_date = db.Column(db.DateTime, default=datetime.utcnow)
