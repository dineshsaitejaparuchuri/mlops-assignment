#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
PAYLOAD='{"age":57,"sex":1,"cp":4,"trestbps":140,"chol":241,"fbs":0,"restecg":0,"thalach":123,"exang":1,"oldpeak":0.2,"slope":2,"ca":0,"thal":7}'

for i in $(seq 1 30); do
  if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then break; fi
  if [ "$i" -eq 30 ]; then echo "health check never succeeded" >&2; exit 1; fi
  sleep 2
done

echo "GET /health"
curl -fsS "$BASE_URL/health"; echo

echo "POST /predict"
curl -fsS -X POST "$BASE_URL/predict" -H 'Content-Type: application/json' -d "$PAYLOAD"; echo

echo "GET /metrics"
curl -fsS "$BASE_URL/metrics" | head -n 5
echo "smoke test passed"
