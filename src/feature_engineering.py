import pandas as pd
import numpy as np

class FeatureEngineer:
    """
    Generates temporal and environmental features for water prediction.
    Prevents data leakage by using strictly historical windows.
    """
    def __init__(self):
        pass

    def add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extracts date-based features."""
        df = df.copy()
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month
            df['quarter'] = df['date'].dt.quarter

            # Define seasons (Northern Hemisphere example)
            # 12,1,2: Winter; 3,4,5: Spring; 6,7,8: Summer; 9,10,11: Autumn
            df['season'] = df['month'].apply(
                lambda x: 'Winter' if x in [12, 1, 2]
                else 'Spring' if x in [3, 4, 5]
                else 'Summer' if x in [6, 7, 8]
                else 'Autumn'
            )
            # Convert season to categorical codes
            df['season_code'] = df['season'].astype('category').cat.codes

        return df

    def add_lag_features(self, df: pd.DataFrame, columns: list, lags: list) -> pd.DataFrame:
        """Creates historical lag features to capture trends.
        Groups by location to prevent cross-location lag contamination.
        """
        df = df.copy()
        if 'location' in df.columns:
            for col in columns:
                if col in df.columns:
                    for lag in lags:
                        df[f"{col}_lag_{lag}"] = df.groupby('location')[col].shift(lag)
        else:
            # Fallback if location is not present
            for col in columns:
                if col in df.columns:
                    for lag in lags:
                        df[f"{col}_lag_{lag}"] = df[col].shift(lag)
        return df

    def add_rolling_features(self, df: pd.DataFrame, columns: list, windows: list) -> pd.DataFrame:
        """Creates rolling mean features for smoothing and trend analysis.
        Groups by location to prevent cross-location contamination.
        """
        df = df.copy()
        if 'location' in df.columns:
            for col in columns:
                if col in df.columns:
                    for window in windows:
                        df[f"{col}_roll_{window}"] = df.groupby('location')[col].transform(lambda x: x.rolling(window=window).mean())
        else:
            # Fallback if location is not present
            for col in columns:
                if col in df.columns:
                    for window in windows:
                        df[f"{col}_roll_{window}"] = df[col].rolling(window=window).mean()
        return df

    def engineer_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full feature engineering pipeline."""
        # 1. Temporal
        df = self.add_temporal_features(df)

        # 2. Lag features for key indicators
        key_cols = ['rainfall', 'groundwater_level', 'reservoir_storage']
        df = self.add_lag_features(df, key_cols, [1, 3, 6])

        # 3. Rolling averages
        df = self.add_rolling_features(df, key_cols, [3, 6])

        # Drop rows with NaNs created by lags/rolling
        return df.dropna()
