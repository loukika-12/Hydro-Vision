import unittest
import json
import os
from config.config import Config
from src.preprocessing import DataPreprocessor
from src.risk_classifier import RiskClassifier
from src.alert_engine import AlertEngine
from src.target_definition import WaterAvailabilityIndex
import pandas as pd
import numpy as np

class TestHydroVision(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.preprocessor = DataPreprocessor(self.config)
        self.classifier = RiskClassifier(self.config)
        self.alert_engine = AlertEngine()
        self.wai = WaterAvailabilityIndex()

    def test_preprocessing_cleaning(self):
        """Test if duplicates are removed and columns standardized."""
        data = {
            'Date': ['2023-01-01', '2023-01-01', '2023-01-02'],
            'Rainfall ': [10, 10, 20],
            'Location': ['Loc1', 'Loc1', 'Loc1']
        }
        df = pd.DataFrame(data)
        cleaned = self.preprocessor.clean_data(df)
        self.assertEqual(len(cleaned), 2)
        self.assertIn('rainfall', cleaned.columns)

    def test_risk_classification(self):
        """Test if availability values map to correct risk levels."""
        self.assertEqual(self.classifier.classify(90), "LOW")
        self.assertEqual(self.classifier.classify(70), "MODERATE")
        self.assertEqual(self.classifier.classify(50), "HIGH")
        self.assertEqual(self.classifier.classify(10), "CRITICAL")

    def test_alert_generation(self):
        """Test if alerts are generated for high risk and suppressed for low risk."""
        alert_high = self.alert_engine.generate_alert(
            "City A", "June 2027", 30.0, "HIGH", ["Low Rainfall"]
        )
        self.assertIsNotNone(alert_high)
        self.assertEqual(alert_high['risk_level'], "HIGH")

        alert_low = self.alert_engine.generate_alert(
            "City B", "June 2027", 90.0, "LOW", ["High Rainfall"]
        )
        self.assertIsNone(alert_low)

    def test_wai_calculation(self):
        """Test if WAI produces values within 0-100 range."""
        data = {
            'rainfall': [100, 200],
            'groundwater_level': [10, 20],
            'reservoir_storage': [50, 80],
            'water_demand': [1000, 2000]
        }
        df = pd.DataFrame(data)
        wai_values = self.wai.calculate_wai(df)
        self.assertTrue(all(wai_values >= 0))
        self.assertTrue(all(wai_values <= 100))

if __name__ == "__main__":
    unittest.main()
