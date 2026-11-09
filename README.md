# HydroVision: Integrated Water Crisis Prediction and Decision Support System

## Overview
HydroVision is an existing Flask decision-support application for water-resource monitoring, water-availability modelling, risk classification, alerts, and GIS suitability analysis. This repository retains the current application and adds a separate, reproducible real-data ingestion workflow.

## Existing application
- Flask + Flask-SQLAlchemy + SQLite backend
- XGBoost regression pipeline and feature engineering
- Water Availability Index (WAI) proxy target
- Risk classification, alert and recommendation modules
- Leaflet/Chart.js dashboard

**Research integrity note:** the existing `data/raw/water_resources_demo.csv`, database seed values, and some dashboard values are demonstration/mock data. They must not be described as measured field observations or real model results. The legacy seed script currently creates random availability values and hard-coded model metrics; do not use those metrics in a paper or evaluation.

## Real-data ingestion (new, additive workflow)
See [Real Data Integration Guide](docs/REAL_DATA_INTEGRATION.md).

Configured sources:
- [Kaggle India Rainfall](https://www.kaggle.com/datasets/aksahaha/rainfall-india)
- [CGWB groundwater dataset](https://huggingface.co/datasets/Daksh17440/india_gwl)
- [Official CGWB quarterly groundwater portal](https://nwdp.nwic.gov.in/dataset/gwl-manual-quarterly-central-ground-water-board-department)
- [Official CWC reservoir data](https://nwdp.nwic.gov.in/en/dataset/reservoir-water-level-manual-daily-centre-water-commission_cwc)

The ingestion workflow does not assume that subdivision, monitoring-station, and reservoir names are interchangeable. It requires an explicit, referenced location crosswalk and creates a quarterly strict intersection only where all three source families overlap. It does not fabricate water demand. Because measured demand is not yet configured and the current WAI requires it, the prepared real observations are **not yet a valid WAI training dataset**.

### Quick start
```bash
python -m pip install -r requirements.txt
python scripts/download_datasets.py
# Save original CGWB and CWC exports under data/raw/sources/
# Create config/location_crosswalk.csv from config/location_crosswalk.example.csv
# Verify every mapping against official geography/station documentation.
python scripts/prepare_water_dataset.py
```

Kaggle credentials must be configured outside source control using `KAGGLE_USERNAME` and `KAGGLE_KEY`, or `~/.kaggle/kaggle.json`. Never commit credentials or source files unless the source license explicitly permits redistribution.

The ETL writes `data/processed/water_resources_real_quarterly.csv` and `reports/real_dataset_report.json`. It will stop if required inputs are missing or if no verified common records exist. Raw files are preserved and the existing demo CSV is not overwritten.

## Setup and run the existing Flask app
```bash
python -m pip install -r requirements.txt
python app.py
``
Open `http://127.0.0.1:5000`.

The legacy `database/seed.py` is for the old demo flow only and currently inserts mock availability and hard-coded metrics. Do not run it when preparing research results. Real-data database seeding and dashboard provenance wiring remain gated on a verified integrated dataset and a reviewed demand/WAI definition.

## Model metrics
No model-performance claim is published here for the real datasets. The prior README's approximate R² claim is not reproducibly established by the source/data audit and should not be cited. Re-train and report metrics only after the real-data target, leakage-safe normalization, location-aware chronological split, and inference feature schema are corrected and independently tested.

## Important limitations
- No satellite imagery is currently acquired or processed by this ingestion workflow.
- Water demand is unavailable until a traceable compatible measurement source is selected.
- The existing demo database seed and dashboard mock KPIs are not real observations.
- A successful ETL run does not establish hydrological equivalence between a rainfall subdivision, groundwater station, and reservoir; crosswalk references and study-boundary justification are required.
