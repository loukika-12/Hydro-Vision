# HydroVision — Water Intelligence

HydroVision is a Flask-based water resource decision-support demo. The responsive dashboard combines model-estimated water availability, risk categories, historical indicators, database alerts, GIS harvesting-site suitability, and model performance information.

## Features
- Regional overview with availability estimate, risk interpretation, recorded groundwater and reservoir values, and trend chart.
- Historical water observations in a chart and table.
- Plain-language guidance for Low, Moderate, High and Critical risk levels.
- Map of demo rainwater-harvesting locations and weighted-overlay suitability scores.
- Active alerts recorded in the project database.
- Model pipeline explanation and evaluation metrics.

## Run locally (Python 3.10+)
```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000. The app creates its database and seeds demo rows on startup if the database is empty.

## Deploy on Render
The repository includes a Render Blueprint file, `render.yaml`. In Render, create a new Blueprint Instance from this repository and deploy the `hydrovision` web service. The service installs requirements and starts Gunicorn on Render's assigned port. SQLite data on a typical web service may not persist across redeployments; for retained data configure managed PostgreSQL and set `DATABASE_URL`.


## Project documentation

The full project report is available in **[docs/PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md)**. It covers the problem statement, requirements, architecture diagrams, data/database design, ML workflow, GIS suitability workflow, API endpoints, setup, testing, limitations, and future enhancements.

## System design

HydroVision follows a layered design:

1. **Presentation layer:** HTML, CSS, and JavaScript provide the responsive dashboard. Chart.js renders availability trends; Leaflet renders sample rainwater-harvesting suitability points.
2. **API/application layer:** Flask serves the dashboard and JSON endpoints for locations, predictions, historical data, alerts, GIS suitability, metrics, and health checks.
3. **Prediction layer:** the feature-engineering pipeline creates date, lag, and rolling features. The saved XGBoost model estimates availability, and the risk classifier maps the estimate to Low, Moderate, High, or Critical.
4. **Decision-support layer:** the alert workflow records an active demo warning for Moderate-or-higher predictions and resolves the region's active warnings when the latest classification is Low. The GIS analyzer computes weighted-overlay suitability scores for sample candidate sites.
5. **Persistence and data layer:** SQLAlchemy models store environmental observations, predictions, alerts, and model metrics. CSV files provide the included demo observations and site data; model metadata stores the expected feature columns and evaluation values.
6. **Deployment layer:** Render starts the Flask application with Gunicorn. Configure managed PostgreSQL through `DATABASE_URL` if records must persist reliably across deployments.

### Architecture diagram

~~~mermaid
flowchart TD
    U[User] --> WEB[Dashboard: HTML / CSS / JavaScript]
    WEB <--> API[Flask JSON API]
    API <--> DB[(SQLAlchemy Database)]
    API --> HIST[Historical observations]
    HIST --> FE[Feature engineering]
    FE --> MODEL[XGBoost model]
    MODEL --> RISK[Risk classification]
    RISK --> PRED[Save prediction]
    RISK --> ALERT[Create/update/resolve alert]
    PRED --> DB
    ALERT --> DB
    API --> GIS[GIS weighted overlay]
    GIS --> SITES[Demo site CSV + configured weights]
    API --> METRICS[Model metrics / metadata]
    API --> WEB
~~~

### Main request flow

When a user selects a region, the dashboard requests its prediction and history. The API loads the region's ordered records, engineers features, aligns them with the saved model's feature columns, estimates availability, applies risk thresholds, stores the prediction, and synchronizes the active alert record. The dashboard then displays the result. The historical endpoint returns observed availability where available and attempts to provide model estimates for missing values; these estimates must not be presented as measured observations.

## Implementation plan

The checklist below separates current prototype capabilities from work needed before real-world use.

### Phase 1 — Core prototype

- [x] Flask application and JSON API.
- [x] SQLAlchemy data models for water data, predictions, alerts, and metrics.
- [x] XGBoost model artifact and feature-engineering pipeline.
- [x] Configurable risk classification.
- [x] Dashboard sections for overview, history, risk, GIS sites, alerts, and model details.
- [x] Demo CSV data and weighted-overlay suitability scoring.
- [x] Render deployment configuration and startup script.
- [x] Project documentation and in-app user guide.

### Phase 2 — Data and workflow reliability

- [x] Persist generated predictions.
- [x] Synchronize database-backed warning records with prediction risk.
- [x] Attempt model-based estimates where historical availability is missing.
- [ ] Verify all endpoints against the deployed environment after each release.
- [ ] Add automated API tests for empty datasets, insufficient history, model errors, and database failures.
- [ ] Label observed values and model estimates consistently in every chart, table, and export.
- [ ] Add a visible data freshness timestamp and source/provenance indicators.

### Phase 3 — Research validation

- [ ] Integrate authoritative water-resource datasets and document licensing, units, geography, and update cadence.
- [ ] Define and validate the water-availability target variable.
- [ ] Re-evaluate the model using a time-aware holdout and baseline comparisons.
- [ ] Validate model performance across locations and seasons; report uncertainty and limitations.
- [ ] Review scarcity thresholds with water-resource domain experts.
- [ ] Validate GIS factors, normalization, spatial reference systems, and candidate sites using reliable spatial layers.

### Phase 4 — Production readiness

- [ ] Configure managed PostgreSQL and database migrations.
- [ ] Add access control, secure secrets, input validation, and operational monitoring.
- [ ] Add reviewed notification delivery for alerts, with deduplication and resolution history.
- [ ] Add CI checks, deployment smoke tests, backups, and error monitoring.
- [ ] Conduct usability, accessibility, and mobile testing with representative users.

**Current status:** HydroVision is a functional research/demo prototype. The checkboxes indicate implementation in the repository or planned work; they do not imply that the model or demo data have been validated for operational water-management decisions.


## Demo-data disclaimer
Values in this project are illustrative. Predictions, suitability scores, thresholds and metrics are for prototyping, not official live measurements or emergency advice. Verify conditions with local water authorities before operational decisions.


## Using the application (user guide)

1. Open the deployed site and start on **Overview**. The region selector is near the top of the page.
2. Choose a region. The app requests the model estimate and historical observations for that region. The four summary cards show predicted availability, modelled scarcity risk, latest recorded groundwater depth, and reservoir storage when those values exist.
3. Click **Refresh data** to request the selected region's prediction and history again and reload the alerts list. This does not train the model or fetch new real-world sensor data.
4. Use the left navigation:
   - **Overview** — summary indicators, historical trend, interpretation, and shortcut cards.
   - **Water availability** — chart and table of recorded dates, rainfall, groundwater depth, reservoir storage, and availability. Hover on chart points for details.
   - **Risk analysis** — current model classification and descriptions of Low, Moderate, High, and Critical categories.
   - **Harvesting sites** — map of demo suitability points. Select a marker for its illustrative score. The map buttons switch between sample suitability markers and a regional map view.
   - **Early warnings** — active alerts stored in the database. An empty list means no active records were returned; it does not establish real-world safety.
   - **Model details** — explains the prediction approach and displays model evaluation metrics when available.
   - **How to use** — an in-app guide explaining the main controls and results.
5. Use **Explore HydroVision** shortcut links on Overview to jump to history, risk guidance, or harvesting sites. Click the HydroVision logo to return to the root page.
6. If a chart or map is empty, check that the demo database is seeded, the relevant CSV files exist, and the API calls succeed. On the free Render plan, the first request after inactivity can take a little while.

### Understanding results and limitations

The predicted availability and risk classification are estimates produced from the project's model and available stored records. Groundwater depth and reservoir storage are the latest recorded sample values, not necessarily live measurements. Map scores, alerts, and metrics are demo/research outputs. Do not use this prototype as an official water-safety or emergency-warning service; verify local conditions with responsible authorities.
