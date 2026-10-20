from pathlib import Path

import numpy as np
import pandas as pd

URL = ("https://archive.ics.uci.edu/ml/machine-learning-databases/"
       "heart-disease/processed.cleveland.data")
COLUMNS = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach",
           "exang", "oldpeak", "slope", "ca", "thal", "target"]
OUT_PATH = Path("data/heart_cleaned.csv")


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.replace("?", np.nan).apply(pd.to_numeric)
    # original labels are 0 (healthy) and 1-4 (severity); we only predict presence
    df["target"] = (df["target"] > 0).astype(int)
    return df


def main() -> None:
    raw = pd.read_csv(URL, header=None, names=COLUMNS)
    df = clean(raw)
    OUT_PATH.parent.mkdir(exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH}: {df.shape[0]} rows, {int(df.isna().sum().sum())} missing cells")


if __name__ == "__main__":
    main()
