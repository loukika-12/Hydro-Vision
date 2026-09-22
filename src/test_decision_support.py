import joblib
import pandas as pd
import numpy as np
from config.config import Config
from src.risk_classifier import RiskClassifier
from src.alert_engine import AlertEngine
from src.recommendation_engine import RecommendationEngine

def test_decision_support():
    config = Config()
    classifier = RiskClassifier(config)
    alert_gen = AlertEngine()
    rec_gen = RecommendationEngine()

    # Scenario 1: Critical Scarcity
    val_crit = 15.5
    risk_crit = classifier.classify(val_crit)
    alert_crit = alert_gen.generate_alert(
        "Hyderabad", "June 2027", val_crit, risk_crit, ["Declining Groundwater", "Low Rainfall"]
    )
    recs_crit = rec_gen.get_recommendations(
        risk_crit,
        {"groundwater_level": 35.0, "reservoir_storage": 15.0, "rainfall": 20.0},
        "Hyderabad"
    )

    print(f"--- Scenario: Critical ---\nRisk: {risk_crit}\nAlert: {alert_crit['headline']}\nRecs: {recs_crit}")

    # Scenario 2: Low Risk
    val_low = 85.0
    risk_low = classifier.classify(val_low)
    alert_low = alert_gen.generate_alert(
        "Bangalore", "June 2027", val_low, risk_low, ["High Rainfall"]
    )
    recs_low = rec_gen.get_recommendations(
        risk_low,
        {"groundwater_level": 10.0, "reservoir_storage": 70.0, "rainfall": 400.0},
        "Bangalore"
    )

    print(f"\n--- Scenario: Low ---\nRisk: {risk_low}\nAlert: {alert_low}\nRecs: {recs_low}")

if __name__ == "__main__":
    test_decision_support()
