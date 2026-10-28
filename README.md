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

## Demo-data disclaimer
Values in this project are illustrative. Predictions, suitability scores, thresholds and metrics are for prototyping, not official live measurements or emergency advice. Verify conditions with local water authorities before operational decisions.
