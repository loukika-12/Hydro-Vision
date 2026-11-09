"""Prepare source-specific records and a conservative quarterly intersection.

No fuzzy location matching, synthetic filling, or demand estimation is performed.
See docs/REAL_DATA_INTEGRATION.md before running.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "raw" / "sources"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"


def require_columns(df, cols, label):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{label}: missing required columns {missing}; found {list(df.columns)}")


def load_crosswalk(path: Path) -> pd.DataFrame:
    cw = pd.read_csv(path, dtype=str).fillna("")
    require_columns(cw, ["source", "source_location", "canonical_location_id",
                         "canonical_location_name", "verification_reference"], "crosswalk")
    if cw.duplicated(["source", "source_location"]).any():
        raise ValueError("Crosswalk contains duplicate source/source_location mappings")
    if (cw["verification_reference"].str.strip() == "").any():
        raise ValueError("Every crosswalk mapping needs a verification_reference")
    return cw


def rainfall_quarterly(path: Path, crosswalk: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    require_columns(df, ["SUBDIVISION", "YEAR"], "Kaggle rainfall")
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
              "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    require_columns(df, months, "Kaggle rainfall")
    if df.duplicated(["SUBDIVISION", "YEAR"]).any():
        raise ValueError("Kaggle rainfall has duplicate subdivision/year rows")
    long = df.melt(id_vars=["SUBDIVISION", "YEAR"], value_vars=months,
                   var_name="month_name", value_name="rainfall_mm")
    month_num = {m: i + 1 for i, m in enumerate(months)}
    long["month"] = long["month_name"].map(month_num)
    long["date"] = pd.to_datetime(dict(year=long["YEAR"], month=long["month"], day=1),
                                  errors="coerce")
    long["rainfall_mm"] = pd.to_numeric(long["rainfall_mm"], errors="coerce")
    if (long["rainfall_mm"].dropna() < 0).any():
        raise ValueError("Rainfall values cannot be negative; check source units/schema")
    long = long.dropna(subset=["date", "rainfall_mm"])
    long["quarter"] = long["date"].dt.to_period("Q").astype(str)
    long["source_location"] = long["SUBDIVISION"].astype(str).str.strip()
    long["source"] = "kaggle_rainfall_india"
    long = long.merge(crosswalk, on=["source", "source_location"], how="left", validate="many_to_one")
    mapped = long.dropna(subset=["canonical_location_id"])
    out = mapped.groupby(["canonical_location_id", "canonical_location_name", "quarter"],
                         as_index=False).agg(rainfall_mm=("rainfall_mm", "sum"))
    out["rainfall_source"] = "Kaggle aksahaha/rainfall-india"
    out["rainfall_unit"] = "mm/quarter"
    out["rainfall_quality"] = "source_observation"
    return out, {"input_rows": len(df), "monthly_rows": len(long),
                 "mapped_monthly_rows": len(mapped), "unmatched_monthly_rows": int(long["canonical_location_id"].isna().sum())}


def observation_quarterly(path: Path, crosswalk: pd.DataFrame, source: str,
                          date_col: str, location_col: str, value_col: str,
                          value_name: str, aggregation: str, unit: str):
    df = pd.read_csv(path)
    require_columns(df, [date_col, location_col, value_col], source)
    df = df[[date_col, location_col, value_col]].copy()
    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df["value"] = pd.to_numeric(df[value_col], errors="coerce")
    df["source_location"] = df[location_col].astype(str).str.strip()
    if df.duplicated([date_col, location_col]).any():
        raise ValueError(f"{source}: duplicate date/location observations need source-specific resolution")
    invalid = int(df["date"].isna().sum())
    missing = int(df["value"].isna().sum())
    df = df.dropna(subset=["date", "value"])
    if value_name == "reservoir_storage_percent" and ((df["value"] < 0) | (df["value"] > 100)).any():
        raise ValueError("Reservoir storage_percent must be between 0 and 100; do not pass level or volume")
    if value_name == "groundwater_depth_m" and unit != "m below ground level":
        raise ValueError("Groundwater depth must be converted to metres below ground level before ETL")
    df["quarter"] = df["date"].dt.to_period("Q").astype(str)
    df["source"] = source
    df = df.merge(crosswalk, on=["source", "source_location"], how="left", validate="many_to_one")
    mapped = df.dropna(subset=["canonical_location_id"])
    grouped = mapped.groupby(["canonical_location_id", "canonical_location_name", "quarter"])["value"]
    if aggregation == "mean":
        result = grouped.mean().rename(value_name).reset_index()
    elif aggregation == "last":
        result = (mapped.sort_values("date").groupby(
            ["canonical_location_id", "canonical_location_name", "quarter"], as_index=False
        ).tail(1)[["canonical_location_id", "canonical_location_name", "quarter", "date", "value"]]
          .rename(columns={"value": value_name, "date": f"{value_name}_source_date"}))
    else:
        raise ValueError("aggregation must be mean or last")
    result[f"{value_name}_source"] = source
    result[f"{value_name}_unit"] = unit
    result[f"{value_name}_quality"] = "source_observation"
    return result, {"input_rows": len(pd.read_csv(path)), "invalid_dates": invalid,
                    "missing_values": missing, "mapped_rows": len(mapped),
                    "unmatched_rows": int(df["canonical_location_id"].isna().sum())}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--crosswalk", default=str(ROOT / "config" / "location_crosswalk.csv"))
    p.add_argument("--rainfall", default=str(SOURCE_DIR / "rainfall_india.csv"))
    p.add_argument("--groundwater", default=str(SOURCE_DIR / "groundwater_cgwb.csv"))
    p.add_argument("--reservoir", default=str(SOURCE_DIR / "reservoir_cwc.csv"))
    p.add_argument("--groundwater-date-col", default="date")
    p.add_argument("--groundwater-location-col", default="station")
    p.add_argument("--groundwater-value-col", default="depth_to_water_m")
    p.add_argument("--reservoir-date-col", default="date")
    p.add_argument("--reservoir-location-col", default="reservoir")
    p.add_argument("--reservoir-value-col", default="storage_percent")
    p.add_argument("--reservoir-unit", default="percent")
    args = p.parse_args()

    cw = load_crosswalk(Path(args.crosswalk))
    rain_path = Path(args.rainfall)
    gw_path = Path(args.groundwater)
    res_path = Path(args.reservoir)
    for f in [rain_path, gw_path, res_path]:
        if not f.exists():
            raise SystemExit(f"Required source file not found: {f}")

    rain, rain_report = rainfall_quarterly(rain_path, cw)
    gw, gw_report = observation_quarterly(
        gw_path, cw, "cgwb_groundwater", args.groundwater_date_col,
        args.groundwater_location_col, args.groundwater_value_col,
        "groundwater_depth_m", "last", "m below ground level"
    )
    res, res_report = observation_quarterly(
        res_path, cw, "cwc_reservoir", args.reservoir_date_col,
        args.reservoir_location_col, args.reservoir_value_col,
        "reservoir_storage_percent", "last", args.reservoir_unit
    )
    # Strict inner join: a row exists only where all three source families overlap.
    merged = rain.merge(gw, on=["canonical_location_id", "canonical_location_name", "quarter"],
                        how="inner", validate="one_to_one")
    merged = merged.merge(res, on=["canonical_location_id", "canonical_location_name", "quarter"],
                          how="inner", validate="one_to_one")
    merged["date"] = pd.PeriodIndex(merged["quarter"], freq="Q").to_timestamp(how="end").normalize()
    merged["source_date"] = merged["date"].dt.strftime("%Y-%m-%d")
    merged["location"] = merged["canonical_location_name"]
    merged["water_demand"] = pd.NA
    merged["water_availability"] = pd.NA
    merged["demand_quality"] = "unavailable_no_verified_source"
    merged["data_mode"] = "real_observations"
    merged = merged.sort_values(["canonical_location_id", "date"])
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output = PROCESSED_DIR / "water_resources_real_quarterly.csv"
    merged.to_csv(output, index=False)
    report = {
        "status": "prepared" if len(merged) else "no_common_records",
        "frequency": "quarterly",
        "join_keys": ["canonical_location_id", "quarter"],
        "join_policy": "strict inner join; no fuzzy matching or imputation",
        "aggregation": {
            "rainfall": "sum monthly subdivision rainfall within calendar quarter",
            "groundwater": "last valid station measurement within quarter",
            "reservoir": "last valid reservoir storage observation within quarter"
        },
        "demand": "unavailable; not observed or estimated",
        "sources": {"rainfall": rain_report, "groundwater": gw_report, "reservoir": res_report},
        "integrated_rows": len(merged),
        "integrated_locations": sorted(merged["location"].unique().tolist()) if len(merged) else [],
        "date_min": str(merged["date"].min().date()) if len(merged) else None,
        "date_max": str(merged["date"].max().date()) if len(merged) else None,
        "output": str(output.relative_to(ROOT))
    }
    (REPORT_DIR / "real_dataset_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if merged.empty:
        raise SystemExit("No verified common location-quarter records. No integrated dataset was produced.")


if __name__ == "__main__":
    main()
