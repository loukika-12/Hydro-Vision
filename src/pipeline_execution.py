import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
import os
import json
from src.preprocessing import DataPreprocessor
from src.target_definition import WaterAvailabilityIndex
from src.feature_engineering import FeatureEngineer
from src.train_models import ModelTrainer
from config.config import Config

def run_full_pipeline():
    config = Config()

    # 1. Load Data
    print("Step 1: Loading data...")
    df = pd.read_csv('data/raw/water_resources_demo.csv')

    # 2. Preprocessing
    print("Step 2: Preprocessing...")
    preprocessor = DataPreprocessor(config)
    df = preprocessor.clean_data(df)
    df = preprocessor.handle_missing_values(df)
    df = preprocessor.align_temporal_frequency(df)

    # CRITICAL: Sort by location and date to ensure lag/rolling features are correct
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['location', 'date']).reset_index(drop=True)

    # 3. Target Definition (WAI)
    print("Step 3: Defining target variable (WAI)...")
    wai_engine = WaterAvailabilityIndex()

    # Calculate WAI and extract normalization parameters from the training data
    df['water_availability'] = wai_engine.calculate_wai(df)

    # Save normalization parameters to prevent leakage during inference
    norm_params = {
        'rainfall': {'min': df['rainfall'].min(), 'max': df['rainfall'].max()},
        'groundwater_level': {'min': (-df['groundwater_level']).min(), 'max': (-df['groundwater_level']).max()},
        'reservoir_storage': {'min': df['reservoir_storage'].min(), 'max': df['reservoir_storage'].max()},
        'water_demand': {'min': df['water_demand'].min(), 'max': df['water_demand'].max()},
    }
    with open('models/preprocessing_params.json', 'w') as f:
        import json
        json.dump(norm_params, f, indent=4)
    print("Preprocessing parameters saved to models/preprocessing_params.json")

    # 4. Feature Engineering
    print("Step 4: Engineering features...")
    fe = FeatureEngineer()
    df_featured = fe.engineer_all(df)

    # Define features (X) and target (y)
    # Use a strict list of feature columns to ensure consistency
    feature_cols = [col for col in df_featured.columns if col not in ['date', 'location', 'latitude', 'longitude', 'water_availability', 'season', 'season_code']]
    X = df_featured[feature_cols]
    y = df_featured['water_availability']

    # 5. Model Training & Comparison
    print("Step 5: Training and comparing models...")
    trainer = ModelTrainer(config)
    comparison_df = trainer.train_and_compare(X, y)


    # Save comparison results
    os.makedirs('reports/metrics', exist_ok=True)
    comparison_df.to_csv('reports/metrics/model_comparison.csv', index=False)
    print("Model comparison saved to reports/metrics/model_comparison.csv")

    # 6. XGBoost Optimization
    print("Step 6: Optimizing primary XGBoost model...")
    best_model, metrics = trainer.optimize_xgboost(X, y)

    # 7. Persistence
    print("Step 7: Saving final model...")
    # Pass the exact feature columns used for training to the save method
    trainer.save_model(best_model, metrics, feature_cols=feature_cols)

    print("\nPipeline complete! Model trained and saved successfully.")

    print(f"Final Test Metrics: {metrics}")

if __name__ == "__main__":
    run_full_pipeline()
