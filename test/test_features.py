import numpy as np
import pandas as pd

from src.download_data import clean
from src.features import RAW_FEATURES, add_hr_reserve, build_pipeline
from sklearn.linear_model import LogisticRegression


def test_clean_binarizes_and_drops_question_marks():
    raw = pd.DataFrame({"ca": ["0.0", "?", "2.0"], "target": [0, 2, 4]})
    out = clean(raw)
    assert out["target"].tolist() == [0, 1, 1]
    assert out["ca"].isna().sum() == 1


def test_committed_csv_shape(data):
    assert list(data.columns) == RAW_FEATURES + ["target"]
    assert set(data["target"]) == {0, 1}


def test_hr_reserve_is_fraction_of_age_max(data):
    out = add_hr_reserve(data)
    expected = data["thalach"] / (220 - data["age"])
    assert np.allclose(out["hr_reserve"], expected)


def test_preprocessor_output_has_no_nan_and_scaled_numerics(data):
    prep = build_pipeline(LogisticRegression()).named_steps
    X = prep["features"].transform(data[RAW_FEATURES])
    out = prep["prep"].fit_transform(X)
    assert not np.isnan(out).any()
    assert abs(out[:, 0].mean()) < 1e-6


def test_unseen_category_does_not_break_pipeline(fitted_pipeline, data):
    row = data[RAW_FEATURES].iloc[[0]].copy()
    row["thal"] = 99.0
    row["cp"] = 9
    proba = fitted_pipeline.predict_proba(row)[0, 1]
    assert 0 <= proba <= 1


def test_missing_values_are_imputed(fitted_pipeline, data):
    row = data[RAW_FEATURES].iloc[[0]].copy()
    row[["ca", "thal", "chol"]] = np.nan
    assert fitted_pipeline.predict_proba(row).shape == (1, 2)
