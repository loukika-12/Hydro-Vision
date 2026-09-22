import logging
from typing import Dict, Any, List
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class AlertEngine:
    """
    Generates structured early warning alerts based on
    predicted water scarcity risks.
    """
    def __init__(self):
        pass

    def generate_alert(self,
                      location: str,
                      prediction_period: str,
                      predicted_value: float,
                      risk_level: str,
                      top_features: List[str]) -> Dict[str, Any]:
        """
        Creates a detailed alert object for the dashboard.
        """
        # Only generate alerts for MODERATE and above
        if risk_level == "LOW":
            return None

        # Map risk levels to alert headlines
        headlines = {
            "MODERATE": "WATER MONITORING ADVISORY",
            "HIGH": "WATER SCARCITY WARNING",
            "CRITICAL": "CRITICAL WATER SHORTAGE ALERT"
        }

        # Map risk levels to recommended actions
        actions = {
            "MODERATE": "Increase monitoring frequency and review seasonal allocation.",
            "HIGH": "Implement water conservation measures and initiate groundwater recharge planning.",
            "CRITICAL": "Prioritize emergency water-resource assessment and enforce strict water rationing."
        }

        alert = {
            "id": f"ALT_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "location": location,
            "period": prediction_period,
            "value": round(predicted_value, 2),
            "risk_level": risk_level,
            "headline": headlines.get(risk_level, "WATER NOTICE"),
            "top_factors": top_features,
            "recommended_action": actions.get(risk_level, "Continue monitoring."),
            "status": "ACTIVE"
        }

        logging.info(f"Generated {risk_level} alert for {location}")
        return alert
