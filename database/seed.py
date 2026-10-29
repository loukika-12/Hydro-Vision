import os
import pandas as pd
from database.models import db, WaterData, ModelMetric
from config.config import Config


def _value(row, *names):
    for name in names:
        if name in row.index:
            value = row.get(name)
            if pd.notna(value):
                return float(value)
    return None


def _date_key(location, date_value):
    # Match by calendar month because legacy demo rows use month-end dates,
    # while the synthetic CSV uses month-start dates.
    return (str(location).strip(), date_value.year, date_value.month)


def seed_database():
    """Idempotently seed legacy demo rows and import the synthetic dataset."""
    print("Seeding database...")
    existing_rows = WaterData.query.order_by(WaterData.date.asc()).all()
    existing_by_month = {}
    for item in existing_rows:
        existing_by_month.setdefault(_date_key(item.location, item.date), item)

    # Keep the original environmental demo data for existing locations.
    legacy_path = os.path.join(Config.DATA_RAW, "water_resources_demo.csv")
    if not existing_rows and os.path.exists(legacy_path):
        legacy = pd.read_csv(legacy_path)
        for _, row in legacy.iterrows():
            dt = pd.to_datetime(row["date"]).to_pydatetime()
            location = str(row["location"]).strip()
            item = WaterData(
                date=dt,
                location=location,
                latitude=_value(row, "latitude"),
                longitude=_value(row, "longitude"),
                rainfall=_value(row, "rainfall"),
                temperature=_value(row, "temperature"),
                humidity=_value(row, "humidity"),
                evaporation=_value(row, "evaporation"),
                groundwater_level=_value(row, "groundwater_level"),
                reservoir_storage=_value(row, "reservoir_storage"),
                population=_value(row, "population"),
                water_demand=_value(row, "water_demand"),
                water_availability=_value(row, "water_availability", "availability"),
                data_source="legacy_demo",
            )
            db.session.add(item)
            existing_by_month.setdefault(_date_key(location, dt), item)
        db.session.flush()

    # Import the project's 2019–2025 synthetic data without duplicate months.
    synthetic_path = os.path.join(Config.DATA_RAW, "hydrovision_synthetic_dataset.csv")
    imported = 0
    targets_filled = 0
    if os.path.exists(synthetic_path):
        frame = pd.read_csv(synthetic_path)
        for _, row in frame.iterrows():
            dt = pd.to_datetime(row["date"]).to_pydatetime()
            location = str(row["location"]).strip()
            key = _date_key(location, dt)
            availability = _value(row, "water_availability_pct", "water_availability", "availability")
            current = existing_by_month.get(key)

            if current is not None:
                # Do not overwrite environmental observations. Fill only a missing
                # target and mark it as synthetic so the UI never calls it measured.
                if current.water_availability is None and availability is not None:
                    current.water_availability = availability
                    current.data_source = "mixed_synthetic_target"
                    targets_filled += 1
                continue

            demand_mld = _value(row, "water_demand_mld")
            demand_for_model = demand_mld * 1000.0 if demand_mld is not None else _value(row, "water_demand")
            item = WaterData(
                date=dt,
                location=location,
                latitude=_value(row, "latitude"),
                longitude=_value(row, "longitude"),
                rainfall=_value(row, "rainfall_mm", "rainfall"),
                temperature=_value(row, "temperature_c", "temperature"),
                humidity=_value(row, "humidity_pct", "humidity"),
                evaporation=_value(row, "evaporation_mm_day", "evaporation"),
                groundwater_level=_value(row, "groundwater_depth_m", "groundwater_level"),
                reservoir_storage=_value(row, "reservoir_storage_pct", "reservoir_storage"),
                population=_value(row, "population_estimate", "population"),
                # The existing model was trained against the legacy demand scale.
                # Convert MLD to thousand-litres/day scale for feature compatibility.
                water_demand=demand_for_model,
                water_availability=availability,
                data_source="synthetic_demo",
            )
            db.session.add(item)
            existing_by_month[key] = item
            imported += 1

    if ModelMetric.query.count() == 0:
        db.session.add(ModelMetric(
            model_name="XGBoost",
            mae=1.616769,
            mse=4.391683,
            rmse=2.095635,
            r2=0.970949
        ))

    db.session.commit()
    print(
        "Database seed complete. "
        f"Imported synthetic rows: {imported}; filled synthetic targets: {targets_filled}."
    )


if __name__ == "__main__":
    from app import app
    with app.app_context():
        db.create_all()
        seed_database()
