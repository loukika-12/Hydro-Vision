# HydroVision — Project Documentation

> **Project:** HydroVision: An Integrated Water Crisis Prediction and Decision Support System for Sustainable Water Resource Management  
> **Project type:** Academic research and demonstration prototype  
> **Application:** Flask, XGBoost, SQLAlchemy, Chart.js, Leaflet  
> **Status:** Working prototype; several data and operational capabilities remain demo-grade

## 1. Introduction

Water-resource planning depends on multiple changing factors, including rainfall, groundwater levels, reservoir storage, evaporation, population, and water demand. When these indicators are reviewed separately, it can be difficult to understand potential scarcity patterns early enough to support planning.

**HydroVision** brings these indicators into one web dashboard. It uses a trained XGBoost regression model to estimate water availability, classifies the estimate into a scarcity-risk category, displays historical indicators, records model-generated warnings, and ranks illustrative rainwater-harvesting sites using a weighted-overlay calculation.

The current repository is a research/demo prototype. Its bundled datasets and site scores are illustrative and should not be interpreted as official real-time measurements or operational water-safety advice.

## 2. Problem Statement

Water-resource stakeholders need a consolidated way to explore environmental indicators, estimate potential availability, identify elevated scarcity risk, and compare possible rainwater-harvesting locations. Disconnected datasets and manual analysis can delay interpretation and make it harder to communicate results.

This project addresses the problem by combining a web-based data view, a machine-learning prediction workflow, a rule-based risk classifier, a database-backed alert workflow, and a GIS-style suitability view in one demonstrator.

## 3. Objectives

- Consolidate available water-resource and environmental observations by region.
- Use an XGBoost model to estimate water availability from environmental and historical features.
- Translate model estimates into Low, Moderate, High, or Critical risk categories.
- Present regional indicators and historical trends through a responsive dashboard.
- Generate and store demo early-warning records for Moderate-or-higher predicted risk.
- Score sample rainwater-harvesting locations using configurable weighted-overlay factors.
- Expose model evaluation metrics and document limitations for transparent interpretation.

## 4. Scope and Requirements

### 4.1 Functional requirements

1. List regions available in the water-resource database.
2. Return a regional availability prediction and risk classification.
3. Return historical water observations and availability values or model estimates where the model can calculate them.
4. Create/update active demo alerts for elevated predicted risk and resolve alerts when the latest classification is Low.
5. Display sample harvesting-site coordinates and suitability scores on a map.
6. Show stored model evaluation metrics.
7. Provide a responsive dashboard and a user guide.

### 4.2 Non-functional requirements

- Clear separation between the web interface, API, prediction logic, and persistence layer.
- Understandable error responses and server-side logging.
- Responsive desktop and mobile layouts.
- Configurable model thresholds and GIS factor weights.
- Deployability to a Python web-hosting platform.
- Clear communication that sample data and model outputs are not official live observations.

## 5. System Architecture

The application uses a browser-based dashboard backed by a Flask JSON API. The API reads environmental records from SQLAlchemy models, builds temporal features, invokes the saved XGBoost model, classifies the resulting estimate, and persists predictions and alert state. The GIS endpoint calculates sample-site scores from a CSV and configuration weights.

~~~mermaid
flowchart TD
    U[User / Evaluator] --> UI[Responsive Dashboard<br/>HTML, CSS, JavaScript]
    UI --> API[Flask REST API]
    API --> DB[(SQLAlchemy Database)]
    API --> FE[Feature Engineering]
    FE --> ML[Saved XGBoost Model]
    ML --> RC[Risk Classifier]
    RC --> P[Prediction Record]
    RC --> AW[Alert Workflow]
    P --> DB
    AW --> DB
    API --> HIST[Historical Water Data]
    HIST --> DB
    API --> GIS[GIS Suitability Analyzer]
    GIS --> CSV[Sample Site CSV]
    GIS --> CFG[GIS Weights Configuration]
    API --> MET[Model Metrics]
    MET --> META[Model Metadata / Database]
    API --> UI
~~~

### Main components

| Component | Responsibility |
|---|---|
| Dashboard (templates/index.html, static/) | Presents regional KPIs, charts, risk guidance, alerts, map, and model metrics. |
| Flask application (app.py) | Serves pages and JSON endpoints; coordinates database, model, alert, and GIS workflows. |
| Feature engineering (src/feature_engineering.py) | Adds date features, lag features, and rolling means from historical environmental observations. |
| XGBoost model (models/) | Produces a numeric availability estimate using the trained model artifact and expected feature columns. |
| Risk classifier (src/risk_classifier.py) | Applies thresholds in config/risk_thresholds.json to map the estimate to a risk category. |
| Database (database/models.py) | Defines water observations, predictions, alerts, and model-metric records. |
| GIS analyzer (gis/suitability.py) | Calculates a weighted suitability score for each illustrative candidate site. |
| Demo datasets (data/raw/) | Provide sample water-resource and harvesting-site records. |
| Deployment (render.yaml, render-start.sh) | Defines the Render deployment and startup process. |

## 6. Data and Database Design

### 6.1 Input data

The repository includes a demo water-resource CSV with fields such as date, location, coordinates, rainfall, temperature, humidity, evaporation, groundwater level, reservoir storage, population, and water demand. The input file does **not** provide a measured availability target column in its current checked-in form. Consequently, historical availability may need to be estimated by the model and must be labelled as an estimate, not an observation.

The GIS sample CSV supplies candidate-site coordinates and factors such as rainfall, slope, land use, and groundwater condition. These are demonstration inputs rather than a verified national or municipal GIS inventory.

### 6.2 Data entities

| Entity | Purpose | Important fields |
|---|---|---|
| WaterData | Stores regional environmental observations | date, location, rainfall, groundwater level, reservoir storage, water demand, optional water availability |
| Prediction | Stores generated model estimates | prediction date, location, predicted availability, risk level, model version |
| Alert | Stores active/resolved warning records | location, risk level, message, status, created timestamp |
| ModelMetric | Stores model evaluation metrics | model name, MAE, MSE, RMSE, R², training date |

The application can use SQLite locally. For hosted deployments, configure a managed PostgreSQL database through DATABASE_URL when data must persist across redeployments. A typical ephemeral web-service filesystem should not be treated as durable storage.

### 6.3 Synthetic dataset integration

The repository includes `data/raw/hydrovision_synthetic_dataset.csv` with 504 monthly synthetic records for six example Telangana locations (2019–2025). The import in `database/seed.py` maps its column names to the existing SQLAlchemy schema and deduplicates by location/month. Missing availability targets on matching legacy rows can be filled from the synthetic target; these rows are marked `mixed_synthetic_target`. New rows are marked `synthetic_demo` and legacy rows `legacy_demo`. The API returns source labels so synthetic values are not described as observed measurements.

See the [Dataset Guide](DATASET_GUIDE.md) for the full data dictionary, feature mapping, risk thresholds, target-leakage cautions, and database persistence notes. Synthetic values and labels are suitable for development/testing only, not real-world prediction validation.

## 7. Machine-Learning Workflow

### 7.1 Feature engineering

The feature engineering pipeline derives year, month, quarter, seasonal information, lagged rainfall/groundwater/reservoir values, and rolling means. Lag and rolling features use historical records to represent recent conditions and trends. Rows without the history needed for these features are dropped by the feature-engineering routine, so sufficient chronological records are required.

### 7.2 Prediction flow

~~~mermaid
flowchart TD
    A[Select region] --> B[Load ordered observations]
    B --> C[Build temporal and lag features]
    C --> D{Enough usable rows?}
    D -- No --> E[Return an explanatory API error]
    D -- Yes --> F[Align to saved model feature columns]
    F --> G[XGBoost availability estimate]
    G --> H[Apply risk thresholds]
    H --> I[Persist prediction]
    I --> J{Risk category}
    J -- Moderate / High / Critical --> K[Create or update active demo alert]
    J -- Low --> L[Resolve active alert for region]
    K --> M[Return JSON response]
    L --> M
~~~

### 7.3 Risk classification

The classifier reads the configured threshold values from config/risk_thresholds.json. The intended categories are Low, Moderate, High, and Critical. Thresholds are model rules, not official hydrological standards; they must be calibrated and validated before any real-world use.

### 7.4 Evaluation metrics

The bundled model metadata currently reports the following evaluation values:

| Metric | Stored value | Interpretation |
|---|---:|---|
| MAE | 1.6168 | Mean absolute prediction error in the target's units |
| MSE | 4.3917 | Mean squared prediction error |
| RMSE | 2.0956 | Root mean squared prediction error in the target's units |
| R² | 0.9709 | Proportion of target variance explained on the reported evaluation set |

These are values stored in the project metadata, not a guarantee of future or regional performance. The documentation should not be interpreted as independently validating the training data, test split, or model generalization.

## 8. GIS Rainwater-Harvesting Suitability

The GIS analyzer implements a weighted-overlay style score using configured factors such as rainfall, slope, land use, and groundwater condition. Lower slope is treated as preferable by inverting the normalized slope factor. The final score is displayed as a percentage and mapped to a qualitative suitability class.

The current implementation uses simplified normalization and sample site data. It is a demonstration of the decision-support workflow, not a substitute for a geospatial study using validated raster layers, coordinate reference systems, hydrological constraints, land ownership, soil permeability, and field verification.

## 9. API and User Interface

The principal API routes in the current application are:

| Endpoint | Purpose |
|---|---|
| GET /api/health | Basic application health response |
| GET /api/locations | List regions represented in stored observations |
| GET /api/water-data/<location> | Return history and available/model-estimated availability values |
| GET /api/prediction/<location> | Generate and store the next-cycle estimate and risk category |
| GET /api/alerts | Return active warning records |
| GET /api/gis/suitability | Return sample site suitability scores |
| GET /api/model-metrics | Return stored or metadata-based model metrics |

The interface includes Overview, Water Availability, Risk Analysis, Harvesting Sites, Early Warnings, Model Details, and How to Use sections. It uses Chart.js for plots and Leaflet/OpenStreetMap tiles for the illustrative map.

## 10. Setup and Deployment

### Local setup

Requirements: Python 3.10 or newer is recommended.

~~~bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
python app.py
~~~

Open http://127.0.0.1:5000 in a browser.

### Render deployment

The repository includes Render configuration and a startup script. The service installs dependencies from requirements.txt, initializes database tables, attempts to seed demo rows when the water table is empty, and starts Gunicorn. Set DATABASE_URL to a managed PostgreSQL connection for durable hosted records. After deployment, verify the build and runtime logs and test the API endpoints; a successful page load alone does not prove that predictions, history, alerts, and GIS data are all working.

## 11. Testing and Verification Plan

- Verify /api/health responds successfully.
- Verify /api/locations returns at least one expected demo region.
- Verify a selected region produces a valid numeric prediction and risk label.
- Verify /api/water-data/<location> returns chronological rows and distinguishes observed values from model estimates where possible.
- Verify the availability chart/table handle empty or unavailable values without crashing.
- Verify Moderate-or-higher predictions create/update an active alert and Low predictions resolve it.
- Verify /api/gis/suitability returns valid coordinates and scores.
- Verify /api/model-metrics returns metrics or a clear empty state.
- Check browser console, API response codes, and Render logs after deployment.
- Test desktop/mobile layouts and the user guide navigation.

## 12. Limitations and Risks

- The bundled water-resource dataset is illustrative and does not contain measured availability in its current source CSV.
- Predictions are only as reliable as the training data, feature alignment, evaluation procedure, and model assumptions.
- Historical estimates must not be presented as observed readings.
- Early-warning records are application-generated demo alerts, not messages from an official monitoring authority.
- GIS suitability uses simplified normalization and sample inputs; it is not a validated engineering recommendation.
- Stored evaluation metrics do not by themselves prove model generalization.
- Hosted SQLite data may be lost across redeployments or instance replacement unless durable storage is configured.
- The prototype has no guarantee of real-time sensor ingestion, official alert delivery, or production-grade authentication and authorization.

## 13. Future Enhancements

1. Integrate verified rainfall, groundwater, reservoir, weather, and satellite datasets with clear provenance and refresh timestamps.
2. Obtain or derive a defensible target variable for water availability and document its units and calculation.
3. Re-run model evaluation with a time-aware train/validation/test split and compare against baseline models.
4. Calibrate risk thresholds with domain experts and publish uncertainty alongside point estimates.
5. Improve historical estimates and label observed vs. model-generated values consistently throughout the UI.
6. Add alert deduplication, severity policy, resolution history, and optional email/SMS delivery after appropriate review.
7. Replace illustrative GIS inputs with validated spatial layers, robust normalization, and field-verified candidate locations.
8. Add automated API/UI tests, CI checks, structured logging, and deployment smoke tests.
9. Use managed PostgreSQL, migration tooling, secrets management, and access controls for a production-oriented deployment.
10. Add data freshness indicators, provenance notes, exportable reports, and accessibility improvements.

## 14. Conclusion

HydroVision demonstrates an integrated workflow for water-resource exploration, model-based availability estimation, risk categorization, early-warning record management, and sample rainwater-harvesting suitability analysis. Its principal contribution is the integration of these components into an understandable dashboard. The next stage should prioritize verified data, reproducible model evaluation, explicit uncertainty, persistent infrastructure, and validation with water-resource domain experts before any operational use.
