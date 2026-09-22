import pandas as pd
import numpy as np

class WaterAvailabilityIndex:
    """
    Implements a mathematically defined Water Availability Index (WAI).
    WAI is a derived indicator used as the target variable when observed
    water supply data is unavailable.

    WAI Formula:
    WAI = (w1 * Norm_Rainfall + w2 * Norm_GW + w3 * Norm_Res) / (w4 * Norm_Demand)

    Where Norm_X is the min-max normalization of the variable.
    """
    def __init__(self, weights: dict = None):
        # Default weights based on hydrological importance
        self.weights = weights or {
            "rainfall": 0.4,
            "groundwater": 0.3,
            "reservoir": 0.3,
            "demand": 0.5 # Demand acts as a penalty/divisor
        }

    def normalize(self, series: pd.Series) -> pd.Series:
        if series.max() == series.min():
            return series * 0 + 1.0
        return (series - series.min()) / (series.max() - series.min())

    def calculate_wai(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculates the WAI for a given dataframe.
        Expected columns: rainfall, groundwater_level, reservoir_storage, water_demand
        """
        # Ensure columns exist
        required = ['rainfall', 'groundwater_level', 'reservoir_storage', 'water_demand']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column for WAI: {col}")

        # Normalize indicators
        # Note: groundwater_level is often 'depth to water', so lower value = more water
        # We invert it for the index
        norm_rain = self.normalize(df['rainfall'])
        norm_gw = self.normalize(-df['groundwater_level'])
        norm_res = self.normalize(df['reservoir_storage'])
        norm_demand = self.normalize(df['water_demand'])

        # Calculate Weighted Supply
        supply_score = (
            self.weights['rainfall'] * norm_rain +
            self.weights['groundwater'] * norm_gw +
            self.weights['reservoir'] * norm_res
        )

        # Calculate WAI
        # We add 1 to demand to avoid division by zero and stabilize the index
        wai = (supply_score / (norm_demand * self.weights['demand'] + 1)) * 100

        return wai.clip(0, 100)
