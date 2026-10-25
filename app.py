from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_caching import Cache
from config.config import Config
from database.models import db, WaterData, Prediction, Alert, ModelMetric
import joblib
import os
import pandas as pd
import numpy as np
import json
from datetime import datetime
from src.risk_classifier import RiskClassifier
from src.alert_engine import AlertEngine
from src.recommendation_engine import RecommendationEngine
from src.feature_engineering import FeatureEngineer
from gis.suitability import GISSuitabilityAnalyzer
from pydantic import BaseModel, ValidationError

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Cache configuration
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

# Initialize DB
db.init_app(app)

with app.app_context():
    db.create_all()

# Load ML Model and Decision Logic
MODEL_PATH = os.path.join(Config.MODEL_PATH, 'xgboost_water_availability.pkl')
model = joblib.load(MODEL_PATH)
risk_classifier = RiskClassifier(Config())
alert_engine = AlertEngine()
rec_engine = RecommendationEngine()
feature_eng = FeatureEngineer()
gis_analyzer = GISSuitabilityAnalyzer(Config())

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "system": "HydroVision API"})

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/api/locations', methods=['GET'])
def get_locations():
    # Fetch unique locations from the database
    locations = db.session.query(WaterData.location).distinct().all()
    return jsonify([loc[0] for loc in locations])

@app.route('/api/water-data/<location>', methods=['GET'])
def get_water_data(location):
    # Fetch historical data for a location
    data = WaterData.query.filter_by(location=location).order_by(WaterData.date.desc()).all()
    results = [{
        "date": d.date.isoformat(),
        "rainfall": d.rainfall,
        "groundwater": d.groundwater_level,
        "reservoir": d.reservoir_storage,
        "availability": d.water_availability
    } for d in data]
    return jsonify(results)

@app.route('/api/prediction/<location>', methods=['GET'])
@cache.cached(timeout=600, query_string=True)
def get_prediction(location):
    try:
        # 1. Fetch historical data for the location to build features
        data = WaterData.query.filter_by(location=location).order_by(WaterData.date.asc()).all()
        if not data:
            return jsonify({"error": "No data available for this location"}), 404

        # Convert DB records to DataFrame
        df = pd.DataFrame([{
            "date": d.date,
            "rainfall": d.rainfall,
            "groundwater_level": d.groundwater,
            "reservoir_storage": d.reservoir,
            "location": d.location
        } for d in data])

        # 2. Generate features using the pipeline
        # The model requires lags and rolling means, so we need the historical window
        df_features = feature_eng.engineer_all(df)

        if df_features.empty:
            return jsonify({"error": "Insufficient historical data to generate features"}), 400

        # 3. Use the most recent feature vector for prediction
        latest_features = df_features.iloc[[-1]]

        # Drop non-feature columns (date, season, etc.) to match model input
        # We keep only the columns that were used during training
        cols_to_drop = ['date', 'season', 'location']
        X = latest_features.drop(columns=[c for c in cols_to_drop if c in latest_features.columns])

        pred_val = model.predict(X)[0]
        risk = risk_classifier.classify(pred_val)

        return jsonify({
            "location": location,
            "predicted_availability": round(float(pred_val), 2),
            "risk_level": risk,
            "prediction_period": "Next Cycle",
            "model": "XGBoost"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    alerts = Alert.query.filter_by(status='ACTIVE').all()
    return jsonify([{
        "location": a.location,
        "risk_level": a.risk_level,
        "message": a.message,
        "created_at": a.created_at.isoformat()
    } for a in alerts])

@app.route('/api/gis/suitability', methods=['GET'])
@cache.cached(timeout=1200)
def get_gis_suitability():
    # Generate suitability dynamically based on the raw GIS sites data
    try:
        csv_path = os.path.join(Config.DATA_RAW, 'gis_sites_demo.csv')
        if not os.path.exists(csv_path):
            return jsonify({"error": "GIS data file not found"}), 404

        df_sites = pd.read_csv(csv_path)
        suitability_df = gis_analyzer.analyze_region(df_sites)

        # Convert to list of dicts for JSON response
        data = suitability_df.to_dict(orient='records')
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/model-metrics', methods=['GET'])
def get_metrics():
    metrics = ModelMetric.query.all()
    return jsonify([{
        "model": m.model_name,
        "mae": m.mae,
        "rmse": m.rmse,
        "r2": m.r2
    } for m in metrics])

if __name__ == "__main__":
    app.run(debug=True, port=5000)
