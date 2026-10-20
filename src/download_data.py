from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile

import numpy as np
import pandas as pd

URL = ("https://archive.ics.uci.edu/ml/machine-learning-databases/"
       "heart-disease/processed.cleveland.data")
ZIP_URL = "https://archive.ics.uci.edu/static/public/45/heart+disease.zip"
COLUMNS = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach",
           "exang", "oldpeak", "slope", "ca", "thal", "target"]
OUT_PATH = Path("data/heart_cleaned.csv")


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.replace("?", np.nan).apply(pd.to_numeric)
    # original labels are 0 (healthy) and 1-4 (severity); we only predict presence
    df["target"] = (df["target"] > 0).astype(int)
    return df


def main() -> None:
    try:
        raw = pd.read_csv(URL, header=None, names=COLUMNS)
    except (URLError, OSError, ValueError) as legacy_error:
        print(f"Legacy UCI URL unavailable ({legacy_error}); trying official dataset archive")
        with urlopen(ZIP_URL, timeout=30) as response:
            archive = ZipFile(BytesIO(response.read()))
        entry = next((name for name in archive.namelist()
                      if name.lower().endswith("processed.cleveland.data")), None)
        if entry is None:
            raise RuntimeError("Official UCI archive did not contain processed Cleveland data")
        raw = pd.read_csv(archive.open(entry), header=None, names=COLUMNS)
    df = clean(raw)
    OUT_PATH.parent.mkdir(exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH}: {df.shape[0]} rows, {int(df.isna().sum().sum())} missing cells")


if __name__ == "__main__":
    main()
