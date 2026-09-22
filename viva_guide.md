# HydroVision Viva-Ready Guide

## 1. What problem are we solving?
We are addressing the fragmentation in water resource management. Most systems look at either groundwater, rainfall, or reservoir levels in isolation. HydroVision integrates these into a single "Decision Support System" (DSS) to predict total water availability and risk.

## 2. Why is the problem important?
Water scarcity is a global crisis. By predicting shortage *before* it happens, governments can implement conservation measures, manage reservoir releases, and build recharge structures, preventing economic loss and humanitarian crises.

## 3. Why integrate multiple datasets?
Water availability is a result of a complex system:
- Rainfall is the primary input.
- Reservoirs are the managed storage.
- Groundwater is the strategic reserve.
- Population/Demand is the pressure.
Integrating these allows the model to understand that high rainfall might not prevent scarcity if the population growth is too rapid or reservoirs are leaking.

## 4. Why XGBoost?
XGBoost (Extreme Gradient Boosting) was chosen because:
1. **Non-linear relationships**: Environmental data is rarely linear.
2. **Handling Missing Data**: It has built-in capabilities to handle sparse data.
3. **Performance**: It consistently outperforms Random Forest and Linear Regression on tabular time-series data.

## 5. What is the prediction target?
The target is the **Water Availability Index (WAI)**. Since "Availability" isn't a single measured unit, we developed a mathematically derived index that normalizes supply (Rain + GW + Res) and divides it by Demand. This provides a percentage (0-100%) representing the health of the water resource.

## 6. How are Risk Levels determined?
We use a configurable threshold system:
- **LOW**: $\ge 80\%$ availability.
- **MODERATE**: $60\% - 80\%$.
- **HIGH**: $40\% - 60\%$.
- **CRITICAL**: $< 40\%$.
These are stored in `risk_thresholds.json` to allow expert adjustment.

## 7. How does the GIS module work?
It uses **Weighted Overlay Analysis (WOA)**. We take multiple spatial layers (Slope, Rainfall, Land Use) and assign weights. 
Example: Rainfall (40%) + Low Slope (20%) + Permeable Land (20%) + GW Stress (20%).
The result is a suitability score from 0-100% used to locate the best spots for rainwater harvesting.

## 8. How is data leakage prevented?
We used **Chronological Splitting** instead of random splitting. We ensure that the training set only contains data from the past, and the test set contains the most recent data. All lag features (e.g., `rainfall_lag_1`) are shifted to ensure the model only sees "yesterday's" data to predict "tomorrow's" availability.

## 9. What are the limitations?
- **Data Quality**: The model is only as good as the sensor data (groundwater levels can be sparse).
- **Resolution**: The current GIS analysis is at a site-level; it doesn't account for micro-topography (e.g., a small cliff).

## 10. Future Scope
- **Satellite Integration**: Using Sentinel-2 imagery for real-time surface water mapping.
- **LSTM Integration**: Adding Long Short-Term Memory (LSTM) networks to capture longer seasonal dependencies.
- **Real-time IoT**: Connecting the dashboard to live sensors in reservoirs.
