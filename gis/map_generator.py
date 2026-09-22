import pandas as pd
import numpy as np
import json
import os
from gis.suitability import GISSuitabilityAnalyzer
from config.config import Config

def generate_gis_data():
    """
    Generates a synthetic spatial dataset for suitability analysis.
    """
    np.random.seed(42)
    # Generate 50 potential sites in the Hyderabad region
    num_sites = 50
    data = {
        'site_id': range(1, num_sites + 1),
        'latitude': np.random.uniform(17.3, 17.5, num_sites),
        'longitude': np.random.uniform(78.3, 78.6, num_sites),
        'rainfall': np.random.uniform(600, 1200, num_sites),
        'slope': np.random.uniform(0, 15, num_sites), # 0-15 degrees
        'land_use': np.random.uniform(0, 100, num_sites), # 0=Built-up, 100=Forest
        'groundwater_condition': np.random.uniform(0, 100, num_sites) # 0=Good, 100=Critical
    }
    df = pd.DataFrame(data)
    os.makedirs('data/raw', exist_ok=True)
    df.to_csv('data/raw/gis_sites_demo.csv', index=False)
    print("GIS demo data generated: data/raw/gis_sites_demo.csv")

def run_gis_analysis():
    config = Config()
    # Generate data if not exists
    if not os.path.exists('data/raw/gis_sites_demo.csv'):
        generate_gis_data()

    # Load data
    df = pd.read_csv('data/raw/gis_sites_demo.csv')

    # Analyze
    analyzer = GISSuitabilityAnalyzer(config)
    results_df = analyzer.analyze_region(df)

    # Save results as GeoJSON-like JSON for the frontend map
    results_list = results_df.to_dict(orient='records')
    os.makedirs('data/processed', exist_ok=True)
    with open('data/processed/harvesting_suitability.json', 'w') as f:
        json.dump(results_list, f, indent=4)

    print(f"GIS analysis complete. {len(results_df)} sites analyzed.")
    print("Results saved to data/processed/harvesting_suitability.json")

if __name__ == "__main__":
    run_gis_analysis()
