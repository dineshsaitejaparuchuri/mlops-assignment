#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
HOST_HEADER_ARGS=()
if [ -n "${SMOKE_TEST_HOST:-}" ]; then
  HOST_HEADER_ARGS=(-H "Host: $SMOKE_TEST_HOST")
fi
PAYLOAD='{"age":57,"sex":1,"cp":4,"trestbps":140,"chol":241,"fbs":0,"restecg":0,"thalach":123,"exang":1,"oldpeak":0.2,"slope":2,"ca":0,"thal":7}'

for i in $(seq 1 30); do
  if curl -fsS "${HOST_HEADER_ARGS[@]}" "$BASE_URL/health" >/dev/null 2>&1; then break; fi
  if [ "$i" -eq 30 ]; then echo "health check never succeeded" >&2; exit 1; fi
  sleep 2
done

echo "GET /health"
curl -fsS "${HOST_HEADER_ARGS[@]}" "$BASE_URL/health"; echo

echo "POST /predict"
curl -fsS -X POST "${HOST_HEADER_ARGS[@]}" "$BASE_URL/predict" -H 'Content-Type: application/json' -d "$PAYLOAD"; echo

echo "GET /metrics"
curl -fsS "${HOST_HEADER_ARGS[@]}" "$BASE_URL/metrics" >/dev/null
echo "metrics endpoint OK"
echo "smoke test passed"
