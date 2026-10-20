import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Histogram,
                               generate_latest)

from src.features import RAW_FEATURES
from src.schemas import PatientFeatures, Prediction

MODEL_PATH = Path(os.getenv("MODEL_PATH", "models/model.joblib"))
LOG_PATH = Path(os.getenv("LOG_PATH", "logs/api.log"))

REQUESTS = Counter("api_requests_total", "HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("api_request_latency_seconds", "Request latency", ["path"])
PREDICTIONS = Counter("model_predictions_total", "Predictions served", ["label"])

LABELS = {0: "no heart disease", 1: "heart disease"}


def make_logger() -> logging.Logger:
    log = logging.getLogger("heart_api")
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handlers = [logging.StreamHandler(sys.stdout)]
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(LOG_PATH))
    except OSError:
        pass
    for h in handlers:
        h.setFormatter(fmt)
        log.addHandler(h)
    return log


logger = make_logger()
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    bundle = joblib.load(MODEL_PATH)
    state.update(bundle)
    logger.info("model loaded from %s (threshold=%.2f)", MODEL_PATH, bundle["threshold"])
    yield
    state.clear()


app = FastAPI(title="Heart disease risk API", version="1.0.0", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        elapsed = time.perf_counter() - start
        route = request.scope.get("route")
        path = getattr(route, "path", "/__unmatched__")
        if path != "/metrics":
            REQUESTS.labels(request.method, path, str(status)).inc()
            LATENCY.labels(path).observe(elapsed)
        logger.info("%s %s status=%d latency_ms=%.1f", request.method, path, status,
                    elapsed * 1000)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": "pipeline" in state}


@app.post("/predict", response_model=Prediction)
def predict(patient: PatientFeatures) -> Prediction:
    if "pipeline" not in state:
        raise HTTPException(status_code=503, detail="model not loaded")
    row = pd.DataFrame([patient.model_dump()])[RAW_FEATURES]
    p_disease = float(state["pipeline"].predict_proba(row)[0, 1])
    pred = int(p_disease >= state["threshold"])
    PREDICTIONS.labels(LABELS[pred]).inc()
    return Prediction(prediction=pred, label=LABELS[pred],
                      probability_predicted_class=round(
                          p_disease if pred else 1 - p_disease, 4),
                      probability_disease=round(p_disease, 4))


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
