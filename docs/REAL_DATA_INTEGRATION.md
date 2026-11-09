# Real-data ingestion for HydroVision

This is an additive ingestion workflow. It does not replace the Flask app, the existing
demo CSV, or the current training pipeline until the prepared real dataset has passed
the coverage and quality checks described here.

## Sources and acquisition

| Variable | Source | Geographic / temporal unit | Acquisition |
|---|---|---|---|
| Rainfall | [Kaggle India Rainfall](https://www.kaggle.com/datasets/aksahaha/rainfall-india) | Meteorological subdivision, monthly totals, 1901–2021 | `python scripts/download_datasets.py` |
| Groundwater | [CGWB India groundwater dataset](https://huggingface.co/datasets/Daksh17440/india_gwl) and [official CGWB quarterly portal](https://nwdp.nwic.gov.in/dataset/gwl-manual-quarterly-central-ground-water-board-department) | Monitoring station / observation date; confirm actual file metadata | Download/export manually to `data/raw/sources/groundwater_cgwb.csv` |
| Reservoir | [Official CWC reservoir data](https://nwdp.nwic.gov.in/en/dataset/reservoir-water-level-manual-daily-centre-water-commission_cwc) | Reservoir / observation date; confirm whether exported field is level, volume, or percent | Download/export manually to `data/raw/sources/reservoir_cwc.csv` |
| Demand | No verified measured demand source configured | Not available | Kept null; do not interpret as observed |

The Kaggle download uses the official Kaggle CLI. Install it with
`python -m pip install kaggle`. Configure `KAGGLE_USERNAME` and `KAGGLE_KEY`
as environment variables, or place the downloaded Kaggle API token at
`~/.kaggle/kaggle.json` (restrict permissions to the owner on Linux/macOS).
Never commit the token. The script does not embed credentials.

For CGWB and CWC, save the original downloaded exports unchanged in
`data/raw/sources/`. Record the portal page, exact file name, download date,
license/terms, units, and any portal metadata in `reports/dataset_sources.json`.
The portal exports are not assumed to have stable schemas.

## Input schema

The rainfall adapter expects the Kaggle wide table with `SUBDIVISION`, `YEAR`,
and JAN–DEC columns (monthly millimetres). Groundwater and reservoir exports must
be converted only by column selection, not by changing values, to these headers
(or supply CLI overrides):

- groundwater: `date,station,depth_to_water_m` (depth in metres below ground level)
- reservoir: `date,reservoir,storage_percent` (percentage of full storage)

If CWC supplies water level or storage volume rather than percentage, do not label
it percent. Add a documented unit conversion using official reservoir capacity
metadata before using the percent field. The default adapter expects percentage.

## Geographic matching and frequency

Copy `config/location_crosswalk.example.csv` to
`config/location_crosswalk.csv` and add only independently verified mappings.
Each source location maps to a canonical location ID and must include a
verification reference. The source identifiers are exact-match keys; fuzzy matching
is deliberately disabled.

The output is quarterly:
- monthly subdivision rainfall is summed within each calendar quarter;
- groundwater is the last valid observation in the quarter;
- reservoir storage is the last valid observation in the quarter;
- source families are combined using a strict inner join on canonical location ID
  and calendar quarter.

This is a conservative screening workflow. A rainfall subdivision, groundwater
station, and reservoir are not automatically hydrologically equivalent merely
because they are in the same state or city. Add mappings only where the study
boundary and hydrological relationship are justified.

## Run

```bash
python -m pip install kaggle pandas
python scripts/download_datasets.py
# Place original CGWB/CWC exports in data/raw/sources/
# Create config/location_crosswalk.csv from the example and verify every mapping.
python scripts/prepare_water_dataset.py
```

Optional column overrides are available; run
`python scripts/prepare_water_dataset.py --help`.

The script writes `data/processed/water_resources_real_quarterly.csv` and
`reports/real_dataset_report.json`. It exits without producing an integrated file
if any source file is absent or if the strict intersection is empty. The report
records row counts, unmatched mappings, invalid dates, missing values, coverage,
and integrated locations.

## WAI and model safeguards

Water demand is intentionally null until a traceable measured source and compatible
geography/frequency are provided. The current WAI formula requires demand, and its
current normalization is fitted on the full dataset before the train/test split.
Therefore the real quarterly output is **not yet a valid WAI training dataset** and
must not be passed into the current training pipeline as if WAI were observed.
Do not impute missing demand, groundwater, or reservoir observations with random
values or global averages. Fit normalization on training data only, preserve the
same parameters for inference, and use a chronological split that respects dates
across all locations before publishing real-data model metrics.

The existing `data/raw/water_resources_demo.csv` remains a separate demonstration
artifact. It is not overwritten by this workflow. Existing database seed code and
dashboard widgets currently contain mocked values; the real-data mode must not be
enabled until database provenance fields and UI labels are wired to the prepared
dataset and the inference schema is validated.

## License and citation

Review each source's current license/terms on its download page before redistribution.
A public download page is not, by itself, proof that raw data may be republished.
Keep original files out of Git unless redistribution rights are explicit. This
workflow records source URLs but does not make a legal determination about licenses.
