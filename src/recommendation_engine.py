import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class RecommendationEngine:
    """
    Rule-based decision support system that provides
    specific actions based on environmental indicators.
    """
    def __init__(self):
        pass

    def get_recommendations(self,
                           risk_level: str,
                           indicators: Dict[str, float],
                           location: str) -> List[str]:
        """
        Analyzes the state of indicators to provide targeted advice.
         Indicators expected: {'groundwater_level': ..., 'reservoir_storage': ..., 'rainfall': ...}
        """
        recs = []

        # 1. Risk-based high-level recommendations
        if risk_level == "CRITICAL":
            recs.append("PRIORITY: Initiate emergency water-resource assessment immediately.")
        elif risk_level == "HIGH":
            recs.append("Initiate regional water conservation planning.")

        # 2. Indicator-based specific recommendations
        # Groundwater logic: if depth is increasing (meaning water table is dropping)
        if 'groundwater_level' in indicators and indicators['groundwater_level'] > 20: # Example threshold
            recs.append("High groundwater depth detected. Implement artificial recharge structures (e.g., check dams).")

        # Reservoir logic: if storage is low
        if 'reservoir_storage' in indicators and indicators['reservoir_storage'] < 40:
            recs.append("Low reservoir storage. Optimize irrigation schedules and reduce industrial withdrawal.")

        # Rainfall logic: if rainfall is below a baseline
        if 'rainfall' in indicators and indicators['rainfall'] < 100:
            recs.append("Below-average precipitation. Prioritize rainwater harvesting from all rooftop surfaces.")

        # Fallback
        if not recs:
            recs.append("Maintain current water management strategy and continue monitoring.")

        return recs
