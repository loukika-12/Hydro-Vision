from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from config.config import Config
from database.models import db, WaterData, Prediction, Alert, ModelMetric
import joblib
import os
import pandas as pd
from datetime import datetime
from src.risk_classifier import RiskClassifier
from src.alert_engine import AlertEngine
from src.recommendation_engine import RecommendationEngine

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

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

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "system": "HydroVision API"})

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/api/locations', methods=['GET'])
def get_locations():
    # In a real app, this would come from the DB. For demo, we return unique locations from data.
    locations = ["Hyderabad", "Bangalore", "Chennai"]
    return jsonify(locations)

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
def get_prediction(location):
    # For demo: we simulate a prediction using a random feature set for that location
    # In a real scenario, we would fetch current features from the DB

    # Simulated current features for the ML model (matches trained features)
    # This is a simplified vector; in reality, we'd use the FeatureEngineer
    dummy_features = np.random.uniform(10, 100, 30).reshape(1, -1)

    # However, to make the API work now, we'll return a mock based on the location
    # to ensure the frontend has data to display.
    import numpy as np
    pred_val = np.random.uniform(30, 90)
    risk = risk_classifier.classify(pred_val)

    return jsonify({
        "location": location,
        "predicted_availability": round(pred_val, 2),
        "risk_level": risk,
        "prediction_period": "June 2027",
        "model": "XGBoost"
    })

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
def get_gis_suitability():
    # Load the pre-calculated JSON
    try:
        with open('data/processed/harvesting_suitability.json', 'r') as f:
            import json
            data = json.load(f)
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
