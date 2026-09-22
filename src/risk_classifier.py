import json
import logging
from typing import Dict, Any
from config.config import Config

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class RiskClassifier:
    """
    Translates continuous water availability predictions into
    discrete risk categories based on configurable thresholds.
    """
    def __init__(self, config: Config):
        self.config = config
        self.thresholds = self._load_thresholds()

    def _load_thresholds(self) -> Dict[str, float]:
        """Loads risk boundaries from the JSON config file."""
        try:
            with open(self.config.RISK_THRESHOLDS_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading thresholds: {e}. Using defaults.")
            return {"low": 80.0, "moderate": 60.0, "high": 40.0, "critical": 20.0}

    def classify(self, availability_value: float) -> str:
        """
        Classifies the predicted availability into a risk level.
        Logic:
        - value >= low_thresh -> LOW
        - value >= mod_thresh -> MODERATE
        - value >= high_thresh -> HIGH
        - value < critical_thresh -> CRITICAL
        """
        if availability_value >= self.thresholds['low']:
            return "LOW"
        elif availability_value >= self.thresholds['moderate']:
            return "MODERATE"
        elif availability_value >= self.thresholds['high']:
            return "HIGH"
        else:
            return "CRITICAL"

    def get_risk_details(self, risk_level: str) -> Dict[str, Any]:
        """Returns metadata associated with the risk level."""
        details = {
            "LOW": {"color": "green", "severity": 1, "desc": "Normal water availability."},
            "MODERATE": {"color": "yellow", "severity": 2, "desc": "Minor deficit detected. Monitoring recommended."},
            "HIGH": {"color": "orange", "severity": 3, "desc": "Significant water scarcity risk."},
            "CRITICAL": {"color": "red", "severity": 4, "desc": "Extreme water shortage. Immediate action required."}
        }
        return details.get(risk_level, details["LOW"])
