import pandas as pd
import numpy as np
import joblib
import os
import logging
import json
from datetime import datetime
from typing import Tuple, Dict, Any
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class ModelTrainer:
    """
    Handles training, evaluation, and persistence of water availability models.
    Uses TimeSeriesSplit to prevent data leakage.
    """
    def __init__(self, config):
        self.config = config
        self.best_model = None
        self.metrics = {}

    def evaluate_model(self, y_true, y_pred) -> Dict[str, float]:
        """Calculates standard regression metrics."""
        return {
            "MAE": mean_absolute_error(y_true, y_pred),
            "MSE": mean_squared_error(y_true, y_pred),
            "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
            "R2": r2_score(y_true, y_pred)
        }

    def train_and_compare(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """
        Trains multiple baseline models and XGBoost to find the best performer.
        Uses a strict chronological split to prevent leakage.
        """
        logging.info("Starting model comparison...")

        # Strict chronological split (First 80% for training, last 20% for testing)
        # Ensure data is sorted by date before this
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        models = {
            "LinearRegression": LinearRegression(),
            "RandomForest": RandomForestRegressor(n_estimators=100, random_state=self.config.RANDOM_STATE),
            "GradientBoosting": GradientBoostingRegressor(random_state=self.config.RANDOM_STATE),
            "XGBoost": XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=self.config.RANDOM_STATE)
        }

        comparison_results = []

        for name, model in models.items():
            logging.info(f"Training {name}...")
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            metrics = self.evaluate_model(y_test, preds)
            metrics['model'] = name
            comparison_results.append(metrics)

        comparison_df = pd.DataFrame(comparison_results)
        return comparison_df

    def optimize_xgboost(self, X: pd.DataFrame, y: pd.Series):
        """
        Performs hyperparameter tuning for the primary XGBoost model.
        """
        logging.info("Optimizing XGBoost hyperparameters...")

        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.1, 0.2],
            'subsample': [0.8, 1.0]
        }

        xgb = XGBRegressor(random_state=self.config.RANDOM_STATE)

        # TimeSeriesSplit for cross-validation
        tscv = TimeSeriesSplit(n_splits=3)

        grid_search = GridSearchCV(
            estimator=xgb,
            param_grid=param_grid,
            cv=tscv,
            scoring='neg_mean_absolute_error',
            n_jobs=-1
        )

        grid_search.fit(X_train, y_train)
        self.best_model = grid_search.best_estimator_

        # Final evaluation on test set
        preds = self.best_model.predict(X_test)
        self.metrics = self.evaluate_model(y_test, preds)

        logging.info(f"Best Params: {grid_search.best_params_}")
        logging.info(f"Final Test Metrics: {self.metrics}")

        return self.best_model, self.metrics

    def save_model(self, model, metrics, feature_cols=None):
        """Persists model, metadata, and feature schema to disk."""
        os.makedirs(self.config.MODEL_PATH, exist_ok=True)

        model_file = os.path.join(self.config.MODEL_PATH, 'xgboost_water_availability.pkl')
        joblib.dump(model, model_file)

        meta_file = os.path.join(self.config.MODEL_PATH, 'model_metadata.json')
        meta_data = {
            "metrics": metrics,
            "feature_columns": feature_cols,
            "training_date": datetime.now().isoformat()
        }
        with open(meta_file, 'w') as f:
            import json
            json.dump(meta_data, f, indent=4)

        logging.info(f"Model and metadata saved to {self.config.MODEL_PATH}")
