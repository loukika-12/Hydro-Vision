import pandas as pd
import numpy as np

class WaterAvailabilityIndex:
    """
    Implements a mathematically defined Water Availability Index (WAI).

    IMPORTANT: WAI is a DERIVED PROXY TARGET. It should not be treated as observed
    ground truth unless verified against actual measured water supply data.

    WAI Formula:
    WAI = (w1 * Norm_Rainfall + w2 * Norm_GW + w3 * Norm_Res) / (w4 * Norm_Demand + 1) * 100

    Assumptions & Units:
    - Rainfall: mm/year (Normalized 0-1)
    - Groundwater: Depth to water level (m). Lower values = higher availability.
      Calculation uses inverted depth (-depth) for normalization.
    - Reservoir: Storage percentage (0-100%).
    - Demand: Volume (m3/year). Acts as a penalty divisor.
    - Weights: Reflect hydrological importance (Rainfall is highest at 0.4).
    """
    def __init__(self, weights: dict = None, norm_params: dict = None):
        self.weights = weights or {
            "rainfall": 0.4,
            "groundwater": 0.3,
            "reservoir": 0.3,
            "demand": 0.5
        }
        # norm_params should contain {'col': {'min': val, 'max': val}}
        self.norm_params = norm_params

    def normalize(self, series: pd.Series, col_name: str) -> pd.Series:
        """Normalizes using provided parameters to prevent leakage."""
        if self.norm_params and col_name in self.norm_params:
            p = self.norm_params[col_name]
            denom = p['max'] - p['min']
            if denom == 0:
                return series * 0 + 1.0
            return (series - p['min']) / denom

        # Fallback for training: calculate from current series
        if series.max() == series.min():
            return series * 0 + 1.0
        return (series - series.min()) / (series.max() - series.min())

    def calculate_wai(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculates the WAI. Expected columns: rainfall, groundwater_level, reservoir_storage, water_demand
        """
        required = ['rainfall', 'groundwater_level', 'reservoir_storage', 'water_demand']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column for WAI: {col}")

        # Invert groundwater depth (lower depth = more water)
        gw_inverted = -df['groundwater_level']

        norm_rain = self.normalize(df['rainfall'], 'rainfall')
        norm_gw = self.normalize(gw_inverted, 'groundwater_level')
        norm_res = self.normalize(df['reservoir_storage'], 'reservoir_storage')
        norm_demand = self.normalize(df['water_demand'], 'water_demand')

        supply_score = (
            self.weights['rainfall'] * norm_rain +
            self.weights['groundwater'] * norm_gw +
            self.weights['reservoir'] * norm_res
        )

        wai = (supply_score / (norm_demand * self.weights['demand'] + 1)) * 100
        return wai.clip(0, 100)
