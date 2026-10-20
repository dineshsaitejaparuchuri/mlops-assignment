"""Run one prediction from a JSON file using the committed model artifact."""

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from src.features import RAW_FEATURES


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON object containing the 13 input features")
    parser.add_argument("--model", type=Path, default=Path("models/model.joblib"))
    args = parser.parse_args()
    patient = json.loads(args.input.read_text(encoding="utf-8"))
    missing = sorted(set(RAW_FEATURES) - set(patient))
    extra = sorted(set(patient) - set(RAW_FEATURES))
    if missing or extra:
        parser.error(f"feature mismatch; missing={missing}, extra={extra}")
    bundle = joblib.load(args.model)
    probability = float(bundle["pipeline"].predict_proba(
        pd.DataFrame([{name: patient[name] for name in RAW_FEATURES}]))[0, 1])
    prediction = int(probability >= bundle["threshold"])
    result = {
        "prediction": prediction,
        "label": "heart disease" if prediction else "no heart disease",
        "probability_predicted_class": round(
            probability if prediction else 1 - probability, 4),
        "probability_disease": round(probability, 4),
        "decision_threshold": bundle["threshold"],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
