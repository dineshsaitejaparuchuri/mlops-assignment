from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from src.features import RAW_FEATURES, build_pipeline

SAMPLE = {"age": 57, "sex": 1, "cp": 4, "trestbps": 140, "chol": 241, "fbs": 0,
          "restecg": 0, "thalach": 123, "exang": 1, "oldpeak": 0.2, "slope": 2,
          "ca": 0, "thal": 7}


@pytest.fixture(scope="session")
def data() -> pd.DataFrame:
    return pd.read_csv(Path(__file__).resolve().parents[1] / "data" / "heart_cleaned.csv")


@pytest.fixture(scope="session")
def fitted_pipeline(data):
    return build_pipeline(LogisticRegression(max_iter=1000)).fit(
        data[RAW_FEATURES], data["target"])


@pytest.fixture(scope="session")
def model_file():
    return Path(__file__).resolve().parents[1] / "models" / "model.joblib"


@pytest.fixture(scope="session")
def client(model_file):
    from src import api

    api.MODEL_PATH = model_file
    with TestClient(api.app) as c:
        yield c


@pytest.fixture
def unloaded_client(monkeypatch):
    from src import api

    monkeypatch.setattr(api, "state", {})
    with TestClient(api.app) as c:
        yield c
