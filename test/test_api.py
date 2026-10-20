import joblib
import pytest

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
    assert 0.5 <= body["confidence"] <= 1
    assert body["label"] in ("heart disease", "no heart disease")


@pytest.mark.parametrize("field,value", [("age", 5), ("age", 150), ("chol", 5000),
                                         ("sex", 2), ("cp", 0), ("oldpeak", -1),
                                         ("thalach", "fast")])
def test_predict_rejects_out_of_range(client, field, value):
    assert client.post("/predict", json={**SAMPLE, field: value}).status_code == 422


def test_predict_rejects_missing_field(client):
    body = {k: v for k, v in SAMPLE.items() if k != "thal"}
    assert client.post("/predict", json=body).status_code == 422


def test_metrics_exposes_counters(client):
    client.post("/predict", json=SAMPLE)
    text = client.get("/metrics").text
    assert "api_requests_total" in text
    assert "model_predictions_total" in text
    assert "api_request_latency_seconds_bucket" in text


def test_model_artifact_roundtrip(model_file, data):
    bundle = joblib.load(model_file)
    proba = bundle["pipeline"].predict_proba(data[bundle["features"]].head(3))
    assert proba.shape == (3, 2)
    assert 0 < bundle["threshold"] < 1
