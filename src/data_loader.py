import pandas as pd
import numpy as np
import os
import json
from typing import List, Dict, Any

class DataLoader:
    """
    Handles ingestion of multi-source water and environmental data.
    Supports CSV, Excel, and JSON formats.
    """
    def __init__(self, raw_data_dir: str):
        self.raw_data_dir = raw_data_dir

    def load_csv(self, filename: str) -> pd.DataFrame:
        path = os.path.join(self.raw_data_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Data file not found: {path}")
        return pd.read_csv(path)

    def load_excel(self, filename: str) -> pd.DataFrame:
        path = os.path.join(self.raw_data_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Data file not found: {path}")
        return pd.read_excel(path)

    def load_json(self, filename: str) -> pd.DataFrame:
        path = os.path.join(self.raw_data_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Data file not found: {path}")
        with open(path, 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)

    def load_dataset(self, filename: str) -> pd.DataFrame:
        """Automatically detect format and load the dataset."""
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.csv':
            return self.load_csv(filename)
        elif ext in ['.xls', '.xlsx']:
            return self.load_excel(filename)
        elif ext == '.json':
            return self.load_json(filename)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def ingest_multiple_sources(self, source_map: Dict[str, str]) -> Dict[str, pd.DataFrame]:
        """
        Ingests multiple datasets based on a mapping.
        Example source_map: {'rainfall': 'rainfall_data.csv', 'groundwater': 'gw_data.xlsx'}
        """
        datasets = {}
        for key, filename in source_map.items():
            try:
                datasets[key] = self.load_dataset(filename)
                print(f"Successfully loaded {key} from {filename}")
            except Exception as e:
                print(f"Error loading {key} from {filename}: {e}")
        return datasets
