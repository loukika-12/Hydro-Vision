from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_caching import Cache
from config.config import Config
from database.models import db, WaterData, Alert, ModelMetric, Prediction
import joblib, os, pandas as pd, uuid
from datetime import datetime
from sqlalchemy import inspect, text

app=Flask(__name__)
app.config.from_object(Config)
CORS(app)
cache=Cache(app,config={'CACHE_TYPE':'SimpleCache','CACHE_DEFAULT_TIMEOUT':300})
db.init_app(app)
def ensure_schema_compatibility():
    """Apply small additive migrations for databases created by older releases."""
    columns = {column["name"] for column in inspect(db.engine).get_columns("water_data")}
    if "data_source" not in columns:
        db.session.execute(text(
            "ALTER TABLE water_data ADD COLUMN data_source VARCHAR(40) DEFAULT 'legacy_demo'"
        ))
        db.session.commit()


with app.app_context():
    db.create_all()
    try:
        ensure_schema_compatibility()
        from database.seed import seed_database
        # Safe to run on every boot: the importer deduplicates by location/month.
        seed_database()
    except Exception:
        db.session.rollback()
        app.logger.exception("Database schema check or demo-data import failed")

model=joblib.load(os.path.join(Config.MODEL_PATH,'xgboost_water_availability.pkl'))
import json
with open(os.path.join(Config.MODEL_PATH, 'model_metadata.json'), encoding='utf-8') as _meta_file:
    MODEL_FEATURE_COLUMNS = json.load(_meta_file).get('feature_columns', [])
from src.risk_classifier import RiskClassifier
from src.feature_engineering import FeatureEngineer
from gis.suitability import GISSuitabilityAnalyzer
risk_classifier,feature_eng,gis_analyzer=RiskClassifier(Config()),FeatureEngineer(),GISSuitabilityAnalyzer(Config())

def build_model_features(rows):
    frame=pd.DataFrame([{
        'date':x.date,'rainfall':x.rainfall,'temperature':x.temperature,
        'humidity':x.humidity,'evaporation':x.evaporation,
        'groundwater_level':x.groundwater_level,'reservoir_storage':x.reservoir_storage,
        'population':x.population,'water_demand':x.water_demand,'location':x.location
    } for x in rows])
    features=feature_eng.engineer_all(frame)
    if features.empty:
        return features, pd.DataFrame()
    x=features.drop(columns=[c for c in ['date','season','season_code','location'] if c in features.columns]).copy()
    if MODEL_FEATURE_COLUMNS:
        for column in MODEL_FEATURE_COLUMNS:
            if column not in x.columns:
                x[column]=0
        x=x[MODEL_FEATURE_COLUMNS]
    return features, x

def sync_alert(location, risk):
    """Keep one active demo warning per region for moderate-or-higher predicted risk."""
    active=Alert.query.filter_by(location=location,status='ACTIVE').all()
    if risk in ('MODERATE','HIGH','CRITICAL'):
        message={
            'MODERATE':'Model estimate indicates a possible water-scarcity concern. Monitor local conditions.',
            'HIGH':'Model estimate indicates elevated water-scarcity risk. Prioritize conservation and verify local conditions.',
            'CRITICAL':'Model estimate indicates critical water-scarcity risk. Verify immediately with local water authorities.'
        }[risk]
        matching=next((a for a in active if a.risk_level==risk),None)
        for alert in active:
            if alert is not matching:
                alert.status='RESOLVED'
        if matching:
            matching.message=message
            matching.created_at=datetime.utcnow()
        else:
            db.session.add(Alert(id=str(uuid.uuid4()),location=location,risk_level=risk,message=message,status='ACTIVE'))
    else:
        for alert in active:
            alert.status='RESOLVED'
    # The caller commits prediction and alert changes in one transaction.

@app.route('/api/health')
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({
            'status':'healthy',
            'system':'HydroVision API',
            'database':'connected',
            'water_records':WaterData.query.count(),
            'locations':db.session.query(WaterData.location).distinct().count()
        })
    except Exception:
        db.session.rollback()
        app.logger.exception("Health check database query failed")
        return jsonify({'status':'degraded','system':'HydroVision API','database':'unavailable'}),503
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/api/locations')
def get_locations():
    rows=db.session.query(WaterData.location).distinct().order_by(WaterData.location).all()
    return jsonify([row[0] for row in rows if row[0]])
@app.route('/api/water-data/<location>')
def get_water_data(location):
    rows=WaterData.query.filter_by(location=location).order_by(WaterData.date.asc()).all()
    if not rows:
        return jsonify([])
    estimated={}
    try:
        built=build_model_features(rows)
        if isinstance(built,tuple):
            features,x=built
            values=model.predict(x)
            for date_value,value in zip(features['date'],values):
                estimated[pd.Timestamp(date_value).date().isoformat()]=round(float(value),2)
    except Exception:
        app.logger.exception('Historical availability estimates failed for %s',location)
    result=[]
    for x in rows:
        actual=x.water_availability
        estimate=estimated.get(x.date.date().isoformat()) if actual is None else None
        if actual is not None:
            availability_source = x.data_source or 'legacy_demo'
        else:
            availability_source = 'model_estimate' if estimate is not None else 'unavailable'
        result.append({
            'date':x.date.isoformat(),'rainfall':x.rainfall,
            'groundwater':x.groundwater_level,'reservoir':x.reservoir_storage,
            'availability':actual if actual is not None else estimate,
            'availability_source':availability_source,
            'data_source':x.data_source or 'legacy_demo'
        })
    return jsonify(result)
@app.route('/api/prediction/<location>')
def get_prediction(location):
    try:
        rows=WaterData.query.filter_by(location=location).order_by(WaterData.date.asc()).all()
        if not rows:
            return jsonify({'error':'No data available for this location'}),404
        built=build_model_features(rows)
        if not isinstance(built,tuple) or built[0].empty:
            return jsonify({'error':'Not enough historical records to build time-series features. At least seven records are recommended.'}),400
        features,x=built
        pred=float(model.predict(x.iloc[[-1]])[0])
        risk=risk_classifier.classify(pred)
        saved_prediction=Prediction(
            prediction_date=pd.Timestamp.utcnow().to_pydatetime(),
            location=location,
            predicted_availability=round(pred,2),
            risk_level=risk,
            model_version='XGBoost'
        )
        db.session.add(saved_prediction)
        sync_alert(location,risk)
        db.session.commit()
        return jsonify({
            'location':location,
            'predicted_availability':round(pred,2),
            'risk_level':risk,
            'prediction_period':'Next Cycle',
            'model':'XGBoost',
            'alert_status':'ACTIVE' if risk in ('MODERATE','HIGH','CRITICAL') else 'RESOLVED_OR_NOT_REQUIRED'
        })
    except Exception:
        db.session.rollback()
        app.logger.exception('Prediction failed for %s',location)
        return jsonify({'error':'Prediction could not be generated. Check server logs and model feature compatibility.'}),500
@app.route('/api/alerts')
def get_alerts():
    rows=Alert.query.filter_by(status='ACTIVE').order_by(Alert.created_at.desc()).all()
    return jsonify([{'location':x.location,'risk_level':x.risk_level,'message':x.message,'created_at':x.created_at.isoformat()} for x in rows])
@app.route('/api/gis/suitability')
@cache.cached(timeout=1200)
def get_gis_suitability():
    try:
        path=os.path.join(Config.DATA_RAW,'gis_sites_demo.csv')
        if not os.path.exists(path):
            return jsonify({'error':'GIS demo dataset is not available.'}),404
        return jsonify(gis_analyzer.analyze_region(pd.read_csv(path)).to_dict(orient='records'))
    except Exception:
        app.logger.exception('GIS analysis failed')
        return jsonify({'error':'The site suitability analysis could not be completed.'}),500
@app.route('/api/model-metrics')
def get_metrics():
    rows=ModelMetric.query.order_by(ModelMetric.training_date.desc()).all()
    if not rows:
        try:
            with open(os.path.join(Config.MODEL_PATH,'model_metadata.json'),encoding='utf-8') as f:
                values=json.load(f).get('metrics',{})
            return jsonify([{'model':'XGBoost','mae':values.get('MAE'),'rmse':values.get('RMSE'),'r2':values.get('R2')}])
        except (OSError,ValueError):
            return jsonify([])
    return jsonify([{'model':x.model_name,'mae':x.mae,'rmse':x.rmse,'r2':x.r2} for x in rows])
if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=False)
