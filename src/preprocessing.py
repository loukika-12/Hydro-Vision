import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class DataPreprocessor:
    """
    Robust preprocessing pipeline for HydroVision.
    Handles cleaning, temporal alignment, and scientific imputation.
    """
    def __init__(self, config):
        self.config = config

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Basic cleaning: duplicates, column naming, date conversion."""
        logging.info("Cleaning data...")

        # Remove duplicates
        initial_len = len(df)
        df = df.drop_duplicates()
        logging.info(f"Removed {initial_len - len(df)} duplicate records.")

        # Standardize column names
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]

        # Convert dates
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

        return df

    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Scientifically justified imputation.
        Time-series variables: Interpolation or Forward Fill.
        Static/Category: Median or Mode.
        """
        logging.info("Handling missing values...")

        # Separate time-series columns from others
        # These usually require interpolation to preserve trends
        ts_cols = [col for col in df.columns if col not in ['date', 'location', 'latitude', 'longitude']]

        for col in ts_cols:
            if df[col].isnull().any():
                # Use linear interpolation for environmental continuous data
                df[col] = df[col].interpolate(method='linear').ffill().bfill()

        return df

    def detect_outliers(self, df: pd.DataFrame, columns: list, threshold: float = 3.0) -> pd.DataFrame:
        """
        Z-score based outlier detection.
        Replaces extreme outliers with the median to avoid skewing ML models.
        """
        df_cleaned = df.copy()
        for col in columns:
            if col in df.columns:
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                outliers = z_scores > threshold
                median_val = df[col].median()
                df_cleaned.loc[outliers, col] = median_val
                logging.info(f"Handled {outliers.sum()} outliers in {col}")

        return df_cleaned

    def align_temporal_frequency(self, df: pd.DataFrame, frequency: str = 'ME') -> pd.DataFrame:
        """
        Aligns data to a specific frequency (e.g., 'ME' for Month End).
        Aggregates daily data to monthly to match slower-changing indicators.
        """
        if 'date' not in df.columns:
            return df

        df = df.set_index('date')

        # Define aggregation rules
        agg_rules = {}
        for col in df.columns:
            if 'rainfall' in col:
                agg_rules[col] = 'sum'
            elif 'temperature' in col or 'humidity' in col or 'evaporation' in col:
                agg_rules[col] = 'mean'
            elif 'groundwater' in col or 'reservoir' in col:
                agg_rules[col] = 'mean'
            elif 'population' in col:
                agg_rules[col] = 'last'
            else:
                agg_rules[col] = 'mean'

        df_resampled = df.resample(frequency).agg(agg_rules).reset_index()
        return df_resampled

    def generate_preprocessing_report(self, before_df: pd.DataFrame, after_df: pd.DataFrame) -> Dict[str, Any]:
        """Generates a summary report of the preprocessing steps."""
        return {
            "records_before": len(before_df),
            "records_after": len(after_df),
            "missing_before": before_df.isnull().sum().sum(),
            "missing_after": after_df.isnull().sum().sum(),
            "features_count": len(after_df.columns)
        }
