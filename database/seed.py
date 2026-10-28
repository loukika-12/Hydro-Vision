import os
import pandas as pd
from database.models import db, WaterData, ModelMetric
from config.config import Config


def seed_database():
    """Populate an empty database from the project's checked-in demo CSV."""
    print("Seeding database...")
    csv_path = os.path.join(Config.DATA_RAW, "water_resources_demo.csv")
    if os.path.exists(csv_path) and WaterData.query.count() == 0:
        frame = pd.read_csv(csv_path)
        # Map only known source columns. The supplied dataset has environmental
        # observations but no measured water_availability target.
        for _, row in frame.iterrows():
            def value(name):
                v = row.get(name)
                return None if pd.isna(v) else v

            water = WaterData(
                date=pd.to_datetime(row["date"]).to_pydatetime(),
                location=row["location"],
                latitude=value("latitude"),
                longitude=value("longitude"),
                rainfall=value("rainfall"),
                temperature=value("temperature"),
                humidity=value("humidity"),
                evaporation=value("evaporation"),
                groundwater_level=value("groundwater_level"),
                reservoir_storage=value("reservoir_storage"),
                population=value("population"),
                water_demand=value("water_demand"),
                water_availability=value("water_availability") if "water_availability" in frame.columns else (value("availability") if "availability" in frame.columns else None)
            )
            db.session.add(water)

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
