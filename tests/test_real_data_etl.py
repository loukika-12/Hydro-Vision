import tempfile
import unittest
from pathlib import Path
import pandas as pd

from scripts.prepare_water_dataset import load_crosswalk, rainfall_quarterly, observation_quarterly


class RealDataETLTests(unittest.TestCase):
    def test_crosswalk_rejects_duplicate_source_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "crosswalk.csv"
            pd.DataFrame([
                ["cgwb_groundwater", "Station A", "loc-1", "Area A", "watershed", "documented relation", "official ref"],
                ["cgwb_groundwater", "Station A", "loc-1", "Area A", "watershed", "documented relation", "official ref"],
            ], columns=["source", "source_location", "canonical_location_id",
                        "canonical_location_name", "canonical_unit_type", "hydrological_basis", "verification_reference"]).to_csv(path, index=False)
            with self.assertRaises(ValueError):
                load_crosswalk(path)

    def test_rainfall_months_aggregate_to_quarter(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "rain.csv"
            crosswalk = Path(tmp) / "crosswalk.csv"
            row = {"SUBDIVISION": "Telangana", "YEAR": 2020}
            row.update({m: 10 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                                       "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]})
            pd.DataFrame([row]).to_csv(source, index=False)
            pd.DataFrame([["kaggle_rainfall_india", "Telangana", "tel-1", "Telangana",
                           "study_area", "verified study-area relation", "official subdivision reference"]],
                         columns=["source", "source_location", "canonical_location_id",
                                  "canonical_location_name", "verification_reference"]).to_csv(crosswalk, index=False)
            cw = load_crosswalk(crosswalk)
            result, report = rainfall_quarterly(source, cw)
            self.assertEqual(len(result), 4)
            self.assertTrue((result["rainfall_mm"] == 30).all())
            self.assertEqual(report["unmatched_monthly_rows"], 0)

    def test_observation_invalid_dates_are_reported_not_imputed(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "gw.csv"
            crosswalk_path = Path(tmp) / "crosswalk.csv"
            pd.DataFrame({"date": ["not-a-date", "2020-01-10"],
                          "station": ["Station A", "Station A"],
                          "depth_to_water_m": [4.2, 4.5]}).to_csv(source, index=False)
            pd.DataFrame([["cgwb_groundwater", "Station A", "loc-1", "Area A", "watershed", "documented relation", "official ref"]],
                         columns=["source", "source_location", "canonical_location_id",
                                  "canonical_location_name", "verification_reference"]).to_csv(crosswalk_path, index=False)
            cw = load_crosswalk(crosswalk_path)
            result, report = observation_quarterly(
                source, cw, "cgwb_groundwater", "date", "station",
                "depth_to_water_m", "groundwater_depth_m", "last", "m below ground level"
            )
            self.assertEqual(report["invalid_dates"], 1)
            self.assertEqual(len(result), 1)
            self.assertEqual(result.iloc[0]["groundwater_depth_m"], 4.5)


if __name__ == "__main__":
    unittest.main()
