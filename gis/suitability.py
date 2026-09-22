import pandas as pd
import numpy as np
import json
import os
import logging
from typing import List, Dict, Any
from config.config import Config

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class GISSuitabilityAnalyzer:
    """
    Implements Weighted Overlay Analysis (WOA) for Rainwater Harvesting suitability.
    Integrates multiple spatial factors to produce a suitability score.
    """
    def __init__(self, config: Config):
        self.config = config
        self.weights = self._load_gis_config()

    def _load_gis_config(self) -> Dict[str, Any]:
        """Loads weights from the GIS config file."""
        try:
            with open(self.config.GIS_CONFIG_PATH, 'r') as f:
                return json.load(f)['layers']
        except Exception as e:
            logging.error(f"Error loading GIS config: {e}. Using defaults.")
            return {
                "rainfall": {"weight": 0.4},
                "slope": {"weight": 0.2},
                "land_use": {"weight": 0.2},
                "groundwater_condition": {"weight": 0.2}
            }

    def normalize_factor(self, value: float, inverse: bool = False) -> float:
        """Normalizes a value to a 0-1 scale."""
        # In a real system, this would be based on global min/max for the region
        # For demo, we use a standard normalization
        norm = np.clip(value / 100.0, 0, 1) if not inverse else np.clip(1 - (value / 100.0), 0, 1)
        return norm

    def calculate_suitability(self, site_data: Dict[str, float]) -> float:
        """
        Calculates the final suitability score for a specific site.
        site_data example: {'rainfall': 1200, 'slope': 2, 'land_use': 80, 'groundwater_condition': 15}
        """
        score = 0.0
        for layer, params in self.weights.items():
            if layer in site_data:
                val = site_data[layer]
                # Slope is inverse (Lower slope = better)
                is_inverse = (layer == 'slope')
                norm_val = self.normalize_factor(val, inverse=is_inverse)
                score += norm_val * params['weight']

        return score * 100 # Return as percentage

    def classify_suitability(self, score: float) -> str:
        """Maps score to suitability classes."""
        if score >= 80: return "Very High"
        if score >= 60: return "High"
        if score >= 40: return "Moderate"
        if score >= 20: return "Low"
        return "Very Low"

    def analyze_region(self, region_df: pd.DataFrame) -> pd.DataFrame:
        """
        Processes a dataframe of potential sites and calculates suitability.
        """
        logging.info("Analyzing regional suitability for rainwater harvesting...")

        results = []
        for _, row in region_df.iterrows():
            site_data = {
                'rainfall': row.get('rainfall', 0),
                'slope': row.get('slope', 0),
                'land_use': row.get('land_use', 0),
                'groundwater_condition': row.get('groundwater_condition', 0)
            }
            score = self.calculate_suitability(site_data)
            results.append({
                'lat': row['latitude'],
                'lon': row['longitude'],
                'score': round(score, 2),
                'class': self.classify_suitability(score)
            })

        return pd.DataFrame(results)
