"""Download traceable HydroVision source datasets without committing credentials or raw files.

Kaggle rainfall is downloaded with the official Kaggle CLI. CGWB/CWC portal exports
must be downloaded manually because portal formats/access endpoints can change.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "sources"


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    kaggle = shutil.which("kaggle")
    if not kaggle:
        raise SystemExit(
            "Kaggle CLI not found. Install with: python -m pip install kaggle\n"
            "Configure credentials using KAGGLE_USERNAME and KAGGLE_KEY environment "
            "variables, or ~/.kaggle/kaggle.json (chmod 600 on Linux/macOS)."
        )
    if not os.getenv("KAGGLE_USERNAME") or not os.getenv("KAGGLE_KEY"):
        cred = Path.home() / ".kaggle" / "kaggle.json"
        if not cred.exists():
            raise SystemExit(
                "Kaggle credentials missing. Set KAGGLE_USERNAME and KAGGLE_KEY, "
                "or place kaggle.json at ~/.kaggle/kaggle.json. Never commit it."
            )
    cmd = [
        kaggle, "datasets", "download", "-d", "aksahaha/rainfall-india",
        "-p", str(RAW), "--unzip"
    ]
    print("Downloading Kaggle India rainfall dataset...")
    subprocess.run(cmd, check=True)
    print(f"Download complete: {RAW}")
    print("CGWB groundwater and CWC reservoir files require manual portal export.")
    print("Save the original, unmodified exports in data/raw/sources/ and record "
          "their download date and file names in reports/dataset_sources.json.")


if __name__ == "__main__":
    main()
