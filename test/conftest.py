import joblib
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
    return pd.read_csv("data/heart_cleaned.csv")


@pytest.fixture(scope="session")
def fitted_pipeline(data):
    pipe = build_pipeline(LogisticRegression(max_iter=1000))
    return pipe.fit(data[RAW_FEATURES], data["target"])


@pytest.fixture(scope="session")
def model_file(tmp_path_factory, fitted_pipeline):
    path = tmp_path_factory.mktemp("model") / "model.joblib"
    joblib.dump({"pipeline": fitted_pipeline, "threshold": 0.4,
                 "features": RAW_FEATURES}, path)
    return path


@pytest.fixture(scope="session")
def client(model_file):
    from src import api

    api.MODEL_PATH = model_file
    with TestClient(api.app) as c:
        yield c
