import pandas as pd
import numpy as np
import os

def generate_demo_data():
    """
    Generates high-fidelity demonstration data for HydroVision.
    The data follows seasonal cycles and realistic environmental trends.
    """
    np.random.seed(42)
    dates = pd.date_range(start='2015-01-01', end='2024-12-01', freq='ME')
    locations = ['Hyderabad', 'Bangalore', 'Chennai']

    all_data = []

    for loc in locations:
        # Base trends
        rain_base = np.random.uniform(500, 1200)
        gw_base = np.random.uniform(10, 30)
        res_base = np.random.uniform(50, 80)
        pop_base = np.random.uniform(1e6, 1e7)

        for date in dates:
            # Seasonal Rainfall (Peak in June-Sept - Monsoon)
            month = date.month
            rain_mult = 5.0 if month in [6, 7, 8, 9] else 0.2 if month in [1, 2] else 1.0
            rainfall = np.random.normal(rain_base/12, 20) * rain_mult

            # Groundwater: Generally drops during summer (March-May), rises during monsoon
            gw_cycle = -2.0 if month in [3, 4, 5] else 2.0 if month in [7, 8] else 0
            gw_level = gw_base + gw_cycle + np.random.normal(0, 1)

            # Reservoir: Follows rainfall lag
            res_storage = res_base + (rainfall * 0.1) + np.random.normal(0, 5)
            res_storage = np.clip(res_storage, 10, 100)

            # Weather
            temp = 25 + 5 * np.sin(2 * np.pi * (month - 1) / 12) + np.random.normal(0, 2)
            hum = 60 + 20 * np.sin(2 * np.pi * (month - 6) / 12) + np.random.normal(0, 5)
            evap = 2 + 2 * np.sin(2 * np.pi * (month - 1) / 12) + np.random.normal(0, 0.5)

            # Population Growth
            pop = pop_base * (1 + 0.02 * (date.year - 2015))

            # Demand: Higher in summer
            demand_mult = 1.5 if month in [3, 4, 5] else 1.0
            demand = (pop * 0.1) * demand_mult + np.random.normal(0, 1000)

            all_data.append({
                'date': date,
                'location': loc,
                'latitude': 17.38 + np.random.uniform(-0.1, 0.1),
                'longitude': 78.48 + np.random.uniform(-0.1, 0.1),
                'rainfall': max(0, rainfall),
                'temperature': temp,
                'humidity': hum,
                'evaporation': evap,
                'groundwater_level': gw_level,
                'reservoir_storage': res_storage,
                'population': pop,
                'water_demand': demand
            })

    df = pd.DataFrame(all_data)

    # Save to raw data directory
    os.makedirs('data/raw', exist_ok=True)
    df.to_csv('data/raw/water_resources_demo.csv', index=False)
    print("Demo dataset generated: data/raw/water_resources_demo.csv")

if __name__ == "__main__":
    generate_demo_data()
