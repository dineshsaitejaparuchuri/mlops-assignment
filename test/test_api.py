import joblib
import re
import pytest
import numpy as np
from fastapi.testclient import TestClient

from test.conftest import SAMPLE


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["model_loaded"] is True


def test_predict_ok(client):
    r = client.post("/predict", json=SAMPLE)
    assert r.status_code == 200
    body = r.json()
    assert body["prediction"] in (0, 1)
    assert 0 <= body["probability_predicted_class"] <= 1
    assert body["label"] in ("heart disease", "no heart disease")
    p = body["probability_disease"]
    expected = p if body["prediction"] else 1 - p
    assert body["probability_predicted_class"] == pytest.approx(expected, abs=0.0001)


def test_tuned_threshold_prediction_probability_below_half(client, monkeypatch):
    from src import api

    class FixedProbability:
        def predict_proba(self, _row):
            return np.array([[0.70, 0.30]])

    monkeypatch.setitem(api.state, "pipeline", FixedProbability())
    monkeypatch.setitem(api.state, "threshold", 0.26)
    body = client.post("/predict", json=SAMPLE).json()
    assert body["prediction"] == 1
    assert body["probability_disease"] == 0.3
    assert body["probability_predicted_class"] == 0.3


def test_predict_returns_503_when_model_not_loaded():
    from src import api

    old_state = api.state.copy()
    api.state.clear()
    try:
        with TestClient(api.app) as c:
            # TestClient's context loads the committed model, so exercise the route
            # with a client that does not run the lifespan manager.
            api.state.clear()
            assert c.post("/predict", json=SAMPLE).status_code == 503
    finally:
        api.state.clear()
        api.state.update(old_state)


@pytest.mark.parametrize("field,value", [("age", 5), ("age", 150), ("chol", 5000),
                                         ("sex", 2), ("cp", 0), ("oldpeak", -1),
                                         ("thalach", "fast")])
def test_predict_rejects_out_of_range(client, field, value):
    assert client.post("/predict", json={**SAMPLE, field: value}).status_code == 422


def test_predict_rejects_missing_field(client):
    body = {k: v for k, v in SAMPLE.items() if k != "thal"}
    assert client.post("/predict", json=body).status_code == 422


def test_predict_ignores_extra_fields(client):
    response = client.post("/predict", json={**SAMPLE, "unused": "ignored"})
    assert response.status_code == 200


def test_metrics_exposes_counters(client):
    before = client.get("/metrics").text
    before_match = re.search(
        r'api_requests_total\{method="POST",path="/predict",status="200"\} (\d+)', before)
    before_count = int(before_match.group(1)) if before_match else 0
    client.post("/predict", json=SAMPLE)
    text = client.get("/metrics").text
    assert "api_requests_total" in text
    assert "model_predictions_total" in text
    assert "api_request_latency_seconds_bucket" in text
    after_match = re.search(
        r'api_requests_total\{method="POST",path="/predict",status="200"\} (\d+)', text)
    assert after_match is not None
    assert int(after_match.group(1)) > before_count


def test_model_artifact_roundtrip(model_file, data):
    bundle = joblib.load(model_file)
    proba = bundle["pipeline"].predict_proba(data[bundle["features"]].head(3))
    assert proba.shape == (3, 2)
    assert 0 < bundle["threshold"] < 1
