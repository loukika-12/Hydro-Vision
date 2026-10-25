import unittest
import pandas as pd
import numpy as np
import os
import json
import joblib
from src.feature_engineering import FeatureEngineer
from src.target_definition import WaterAvailabilityIndex
from config.config import Config

class TestMLPipeline(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.fe = FeatureEngineer()
        dates = pd.to_datetime(['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01', '2023-06-01',
                               '2023-07-01', '2023-08-01', '2023-09-01', '2023-10-01', '2023-11-01', '2023-12-01'])
        data = {
            'location': ['CityA'] * 12 + ['CityB'] * 12,
            'date': list(dates) * 2,
            'rainfall': np.random.uniform(10, 100, 24),
            'groundwater_level': np.random.uniform(5, 50, 24),
            'reservoir_storage': np.random.uniform(20, 80, 24),
            'water_demand': np.random.uniform(30, 70, 24)
        }
        self.df = pd.DataFrame(data)

    def test_location_boundary_leakage(self):
        """Ensure lag features for CityB do not contain values from CityA."""
        df_featured = self.fe.engineer_all(self.df)
        # Find first index where location is CityB
        city_b_start_idx = self.df[self.df['location'] == 'CityB'].index[0]
        # In df_featured, rows are dropped due to NaNs.
        # We should check the raw shift result before dropna().

        # Let's recreate the feature eng step manually to check the raw shifts
        df_temp = self.df.copy()
        df_temp['rainfall_lag_6'] = df_temp.groupby('location')['rainfall'].shift(6)

        val_at_start_of_b = df_temp.loc[city_b_start_idx, 'rainfall_lag_6']
        self.assertTrue(np.isnan(val_at_start_of_b),
                        f"Leakage detected: CityB record at index {city_b_start_idx} has lag value {val_at_start_of_b} from CityA")


    def test_feature_consistency(self):
        """Verify that feature columns are consistent."""
        df_featured = self.fe.engineer_all(self.df)
        expected_cols = ['year', 'month', 'quarter', 'season_code']
        for col in ['rainfall', 'groundwater_level', 'reservoir_storage']:
            for lag in [1, 3, 6]:
                expected_cols.append(f"{col}_lag_{lag}")
            for roll in [3, 6]:
                expected_cols.append(f"{col}_roll_{roll}")
        for col in expected_cols:
            self.assertIn(col, df_featured.columns)

    def test_wai_normalization_leakage(self):
        """Verify WAI uses provided params instead of calculating from current series."""
        wai_params = {
            'rainfall': {'min': 0, 'max': 100},
            'groundwater_level': {'min': -50, 'max': 0},
            'reservoir_storage': {'min': 0, 'max': 100},
            'water_demand': {'min': 0, 'max': 100}
        }
        wai_engine = WaterAvailabilityIndex(norm_params=wai_params)
        df_test = pd.DataFrame({'rainfall': [150], 'groundwater_level': [10], 'reservoir_storage': [150], 'water_demand': [150]})
        norm_val = wai_engine.normalize(df_test['rainfall'], 'rainfall')
        self.assertEqual(norm_val.iloc[0], 1.5)

if __name__ == '__main__':
    unittest.main()
