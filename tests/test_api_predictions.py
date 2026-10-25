import unittest
import json
import os
import pandas as pd
import numpy as np
from app import app, db, WaterData
from config.config import Config

class TestHydroVisionAPI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            # Seed a location with sufficient history (12 months)
            dates = pd.date_range(start='2023-01-01', periods=12, freq='MS')
            for date in dates:
                data = WaterData(
                    location="ValidCity",
                    date=date,
                    rainfall=100.0,
                    groundwater_level=20.0,
                    reservoir_storage=80.0,
                    water_demand=500000.0
                )
                db.session.add(data)

            # Seed a location with insufficient history (3 months)
            dates_short = pd.date_range(start='2023-01-01', periods=3, freq='MS')
            for date in dates_short:
                data = WaterData(
                    location="ShortCity",
                    date=date,
                    rainfall=100.0,
                    groundwater_level=20.0,
                    reservoir_storage=80.0,
                    water_demand=500000.0
                )
                db.session.add(data)

            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_prediction_success(self):
        """Verify that a location with sufficient history returns 200 OK."""
        response = self.client.get('/api/prediction/ValidCity')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('predicted_availability', data)
        self.assertEqual(data['location'], 'ValidCity')

    def test_prediction_insufficient_history(self):
        """Verify that a location with < 7 months of data returns 400."""
        response = self.client.get('/api/prediction/ShortCity')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Insufficient historical data', json.loads(response.data)['error'])

    def test_prediction_unknown_location(self):
        """Verify that an unknown location returns 404."""
        response = self.client.get('/api/prediction/GhostCity')
        self.assertEqual(response.status_code, 404)

    def test_schema_mismatch_detection(self):
        """Verify that the API detects if the model schema is corrupted."""
        with app.app_context():
            # Temporarily corrupt the metadata file
            meta_path = os.path.join(Config.MODEL_PATH, 'model_metadata.json')
            with open(meta_path, 'r') as f:
                meta = json.load(f)

            original_cols = meta['feature_columns']
            meta['feature_columns'] = ['non_existent_feature_xyz']
            with open(meta_path, 'w') as f:
                json.dump(meta, f)

        try:
            response = self.client.get('/api/prediction/ValidCity')
            self.assertEqual(response.status_code, 400)
            self.assertIn('Feature mismatch', json.loads(response.data)['error'])
        finally:
            # Restore metadata
            with app.app_context():
                with open(meta_path, 'w') as f:
                    json.dump({"feature_columns": original_cols}, f)

if __name__ == '__main__':
    unittest.main()
