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
