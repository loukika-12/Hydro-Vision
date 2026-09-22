# HydroVision: Integrated Water Crisis Prediction and Decision Support System

## 🌊 Overview
HydroVision is a professional-grade decision support platform designed to predict water scarcity and assist in sustainable water resource management. It integrates multi-source environmental data to provide actionable insights for city planners and environmental engineers.

## 🚀 Core Features
- **Water Availability Prediction**: Uses an optimized **XGBoost Regression** model to predict future water availability based on rainfall, groundwater, reservoirs, and population trends.
- **Risk Classification**: Automatically categorizes regions into **Low, Moderate, High, or Critical** risk levels based on configurable scientific thresholds.
- **Early Warning System**: Generates structured alerts for high-risk areas with specific recommended mitigation actions.
- **GIS Suitability Analysis**: Implements **Weighted Overlay Analysis (WOA)** to identify optimal locations for rainwater harvesting and groundwater recharge.
- **Interactive Dashboard**: A full-stack Flask application with real-time KPIs, trend charts (Chart.js), and spatial maps (Leaflet.js).

## 🛠 Tech Stack
- **Backend**: Python 3.10+, Flask, Flask-SQLAlchemy, SQLite.
- **ML/Data Science**: XGBoost, Scikit-Learn, Pandas, NumPy, SciPy.
- **GIS**: GeoPandas, Shapely, Leaflet.js.
- **Frontend**: HTML5, CSS3 (Bootstrap 5), JavaScript (ES6+).

## 📁 Project Structure
```text
HYDROVISION/
├── app.py                  # Flask Application Entry
├── config/                 # System & Risk Configurations
├── data/                   # Raw, Processed, and Featured Datasets
├── models/                 # Saved ML Models (.pkl) and Metadata
├── src/                    # Core Logic (Preprocessing, ML, Alerts, Recs)
├── gis/                    # Spatial Analysis & Suitability Logic
├── database/               # SQLAlchemy Models & DB Seeding
├── templates/              # Frontend HTML
├── static/                 # CSS, JS, and Images
└── tests/                  # Unit & Integration Tests
```

## ⚙️ Installation & Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/loukika-12/HydroVision.git
   cd HydroVision
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database**:
   ```bash
   export PYTHONPATH=.
   python database/seed.py
   ```

5. **Run the Application**:
   ```bash
   python app.py
   ```
   Visit `http://127.0.0.1:5000` in your browser.

## 📊 Model Evaluation
- **Primary Model**: XGBoost Regressor.
- **Performance**: Achieved high $R^2$ ($\approx 0.96$) on the validation set.
- **Validation**: Time-series split used to prevent data leakage.

## 🛡️ Research Integrity
- All data used in the demo is marked as **DEMONSTRATION DATA**.
- The system is built to be modular; replacing `data/raw/*.csv` with real-world observations will allow the pipeline to produce real-world predictions without code changes.
