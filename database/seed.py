import os
import pandas as pd
import numpy as np
from database.models import db, WaterData, ModelMetric
from config.config import Config


def seed_database():
    """Populate an empty database from the checked-in demo water dataset."""
    print("Seeding database...")
    csv_path = os.path.join(Config.DATA_RAW, "water_resources_demo.csv")
    if os.path.exists(csv_path) and WaterData.query.count() == 0:
        frame = pd.read_csv(csv_path)
        # Use the project's documented demo availability field when present.
        for _, row in frame.iterrows():
            value = row.get("water_availability", row.get("availability"))
            if pd.isna(value):
                value = np.nan
            water = WaterData(
                date=pd.to_datetime(row["date"]),
                location=row["location"],
                latitude=row.get("latitude"),
                longitude=row.get("longitude"),
                rainfall=row.get("rainfall"),
                temperature=row.get("temperature"),
                humidity=row.get("humidity"),
                evaporation=row.get("evaporation"),
                groundwater_level=row.get("groundwater_level"),
                reservoir_storage=row.get("reservoir_storage"),
                population=row.get("population"),
                water_demand=row.get("water_demand"),
                water_availability=value
            )
            db.session.add(water)

    # Prefer persisted metrics if they already exist; never add duplicates on re-seed.
    if ModelMetric.query.count() == 0:
        db.session.add(ModelMetric(
            model_name="XGBoost",
            mae=1.616769,
            mse=4.391683,
            rmse=2.095635,
            r2=0.970949
        ))
    db.session.commit()
    print("Database seeded successfully!")


if __name__ == "__main__":
    from app import app
    with app.app_context():
        db.create_all()
        seed_database()
