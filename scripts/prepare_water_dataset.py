"""Prepare traceable source observations; no fuzzy matching or synthetic imputation."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "raw" / "sources"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"
SOURCE_URLS = {
    "rainfall": "https://www.kaggle.com/datasets/aksahaha/rainfall-india",
    "groundwater": "https://nwdp.nwic.gov.in/dataset/gwl-manual-quarterly-central-ground-water-board-department",
    "reservoir": "https://nwdp.nwic.gov.in/en/dataset/reservoir-water-level-manual-daily-centre-water-commission_cwc",
}


def require_columns(df, cols, label):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{label}: missing required columns {missing}; found {list(df.columns)}")


def file_metadata(path: Path, df: pd.DataFrame, date_series=None):
    meta = {
        "file": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "rows": int(len(df)),
        "columns": list(df.columns),
        "missing_cells_percent": round(float(df.isna().sum().sum() / max(1, df.size) * 100), 3),
        "missing_percent_by_column": {
            str(k): round(float(v / max(1, len(df)) * 100), 3)
            for k, v in df.isna().sum().items()
        },
    }
    if date_series is not None:
        dates = pd.to_datetime(date_series, errors="coerce").dropna()
        meta["invalid_date_rows"] = int(pd.to_datetime(date_series, errors="coerce").isna().sum())
        meta["date_min"] = str(dates.min().date()) if len(dates) else None
        meta["date_max"] = str(dates.max().date()) if len(dates) else None
    return meta


def load_crosswalk(path: Path) -> pd.DataFrame:
    cw = pd.read_csv(path, dtype=str).fillna("")
    require_columns(cw, ["source", "source_location", "canonical_location_id",
                         "canonical_location_name", "verification_reference"], "crosswalk")
    if cw.empty:
        raise ValueError("Location crosswalk is empty. Add verified source-to-study-unit mappings.")
    if cw.duplicated(["source", "source_location"]).any():
        raise ValueError("Crosswalk contains duplicate source/source_location mappings")
    if (cw[["verification_reference", "canonical_location_id", "canonical_location_name"]]
            .apply(lambda col: col.str.strip().eq("")).any().any()):
        raise ValueError("Each crosswalk row needs a canonical ID/name and verification reference")
    return cw


def rainfall_quarterly(path: Path, crosswalk: pd.DataFrame):
    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
              "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    require_columns(df, ["SUBDIVISION", "YEAR", *months], "Kaggle rainfall")
    duplicate_rows = int(df.duplicated(["SUBDIVISION", "YEAR"]).sum())
    if duplicate_rows:
        raise ValueError("Kaggle rainfall has duplicate subdivision/year rows")
    raw_meta = file_metadata(path, df)
    long = df.melt(id_vars=["SUBDIVISION", "YEAR"], value_vars=months,
                   var_name="month_name", value_name="rainfall_mm")
    month_num = {m: i + 1 for i, m in enumerate(months)}
    long["month"] = long["month_name"].map(month_num)
    long["date"] = pd.to_datetime(dict(year=long["YEAR"], month=long["month"], day=1),
                                  errors="coerce")
    long["rainfall_mm"] = pd.to_numeric(long["rainfall_mm"], errors="coerce")
    invalid_dates = int(long["date"].isna().sum())
    missing_values = int(long["rainfall_mm"].isna().sum())
    if (long["rainfall_mm"].dropna() < 0).any():
        raise ValueError("Rainfall values cannot be negative; check source units/schema")
    long = long.dropna(subset=["date", "rainfall_mm"])
    long["quarter"] = long["date"].dt.to_period("Q").astype(str)
    long["source_location"] = long["SUBDIVISION"].astype(str).str.strip()
    long["source"] = "kaggle_rainfall_india"
    long = long.merge(crosswalk, on=["source", "source_location"], how="left",
                      validate="many_to_one")
    unmatched = int(long["canonical_location_id"].isna().sum())
    mapped = long.dropna(subset=["canonical_location_id"])
    out = mapped.groupby(["canonical_location_id", "canonical_location_name", "quarter"],
                         as_index=False).agg(rainfall_mm=("rainfall_mm", "sum"))
    out["rainfall_source"] = "Kaggle aksahaha/rainfall-india"
    out["rainfall_unit"] = "mm/quarter"
    out["rainfall_quality"] = "source_observation"
    report = {
        **raw_meta, "monthly_records_after_parse": int(len(long)),
        "invalid_date_records": invalid_dates, "missing_monthly_values": missing_values,
        "unmatched_monthly_records": unmatched, "mapped_monthly_records": int(len(mapped)),
        "integrated_quarterly_records": int(len(out)),
        "mapped_locations": sorted(mapped["source_location"].unique().tolist()),
        "units": "millimetres per month in source; summed to millimetres per calendar quarter",
    }
    return out, report


def observation_quarterly(path: Path, crosswalk: pd.DataFrame, source: str,
                          date_col: str, location_col: str, value_col: str,
                          value_name: str, aggregation: str, unit: str):
    df = pd.read_csv(path)
    require_columns(df, [date_col, location_col, value_col], source)
    raw_meta = file_metadata(path, df, df[date_col])
    duplicate_rows = int(df.duplicated([date_col, location_col]).sum())
    if duplicate_rows:
        raise ValueError(f"{source}: duplicate date/location rows; resolve against source documentation")
    df = df[[date_col, location_col, value_col]].copy()
    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df["value"] = pd.to_numeric(df[value_col], errors="coerce")
    df["source_location"] = df[location_col].astype(str).str.strip()
    invalid = int(df["date"].isna().sum())
    missing = int(df["value"].isna().sum())
    df = df.dropna(subset=["date", "value"])
    if value_name == "reservoir_storage_percent" and ((df["value"] < 0) | (df["value"] > 100)).any():
        raise ValueError("Reservoir storage_percent must be between 0 and 100; do not pass level or volume")
    if value_name == "groundwater_depth_m" and unit != "m below ground level":
        raise ValueError("Groundwater depth must be converted to metres below ground level before ETL")
    df["quarter"] = df["date"].dt.to_period("Q").astype(str)
    df["source"] = source
    df = df.merge(crosswalk, on=["source", "source_location"], how="left",
                  validate="many_to_one")
    unmatched = int(df["canonical_location_id"].isna().sum())
    mapped = df.dropna(subset=["canonical_location_id"])
    keys = ["canonical_location_id", "canonical_location_name", "quarter"]
    if aggregation == "mean":
        result = mapped.groupby(keys)["value"].mean().rename(value_name).reset_index()
    elif aggregation == "last":
        result = (mapped.sort_values("date").groupby(keys, as_index=False).tail(1)
                  [keys + ["date", "value"]]
                  .rename(columns={"value": value_name, "date": f"{value_name}_source_date"}))
    else:
        raise ValueError("aggregation must be mean or last")
    result[f"{value_name}_source"] = source
    result[f"{value_name}_unit"] = unit
    result[f"{value_name}_quality"] = "source_observation"
    report = {
        **raw_meta, "invalid_date_records": invalid, "missing_numeric_values": missing,
        "unmatched_records": unmatched, "mapped_records": int(len(mapped)),
        "integrated_quarterly_records": int(len(result)),
        "mapped_locations": sorted(mapped["source_location"].unique().tolist()),
        "units": unit, "quarterly_aggregation": aggregation,
    }
    return result, report


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
    paths = {"rainfall": Path(args.rainfall), "groundwater": Path(args.groundwater),
             "reservoir": Path(args.reservoir)}
    for f in paths.values():
        if not f.exists():
            raise SystemExit(f"Required source file not found: {f}")

    rain, rain_report = rainfall_quarterly(paths["rainfall"], cw)
    gw, gw_report = observation_quarterly(
        paths["groundwater"], cw, "cgwb_groundwater", args.groundwater_date_col,
        args.groundwater_location_col, args.groundwater_value_col,
        "groundwater_depth_m", "last", "m below ground level")
    res, res_report = observation_quarterly(
        paths["reservoir"], cw, "cwc_reservoir", args.reservoir_date_col,
        args.reservoir_location_col, args.reservoir_value_col,
        "reservoir_storage_percent", "last", args.reservoir_unit)

    merged = rain.merge(gw, on=["canonical_location_id", "canonical_location_name", "quarter"],
                        how="inner", validate="one_to_one")
    merged = merged.merge(res, on=["canonical_location_id", "canonical_location_name", "quarter"],
                          how="inner", validate="one_to_one")
    merged["date"] = pd.PeriodIndex(merged["quarter"], freq="Q").to_timestamp(how="end").normalize()
    merged["location"] = merged["canonical_location_name"]
    merged["water_demand"] = pd.NA
    merged["water_availability"] = pd.NA
    merged["demand_quality"] = "unavailable_no_verified_source"
    merged["data_mode"] = "real_observations"
    merged["source_date"] = merged["date"].dt.strftime("%Y-%m-%d")
    merged = merged.sort_values(["canonical_location_id", "date"])

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output = PROCESSED_DIR / "water_resources_real_quarterly.csv"
    merged.to_csv(output, index=False)
    report = {
        "status": "prepared" if len(merged) else "no_common_records",
        "source_links": SOURCE_URLS,
        "licenses": {
            "rainfall": "Not programmatically verified; inspect Kaggle dataset license before redistribution.",
            "groundwater": "Not programmatically verified; inspect NWIC/CGWB portal terms for the downloaded export.",
            "reservoir": "Not programmatically verified; inspect NWIC/CWC portal terms for the downloaded export.",
        },
        "source_file_reports": {"rainfall": rain_report, "groundwater": gw_report, "reservoir": res_report},
        "frequency": "quarterly",
        "join_keys": ["canonical_location_id", "quarter"],
        "join_policy": "strict inner join; exact source identifiers mapped through user-verified crosswalk; no fuzzy matching or imputation",
        "aggregation": {
            "rainfall": "sum monthly subdivision rainfall within calendar quarter",
            "groundwater": "last valid station measurement in quarter",
            "reservoir": "last valid reservoir storage observation in quarter"
        },
        "demand": "unavailable; not observed or estimated",
        "integrated_rows": int(len(merged)),
        "integrated_locations": sorted(merged["location"].unique().tolist()) if len(merged) else [],
        "date_min": str(merged["date"].min().date()) if len(merged) else None,
        "date_max": str(merged["date"].max().date()) if len(merged) else None,
        "output": str(output.relative_to(ROOT)),
    }
    (REPORT_DIR / "real_dataset_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if merged.empty:
        raise SystemExit("No verified common location-quarter records. No integrated dataset was produced.")


if __name__ == "__main__":
    main()
