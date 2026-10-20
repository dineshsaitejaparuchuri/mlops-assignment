# Demo video script (about 5-6 min)

Run everything from the repo root with the venv active (`source .venv/bin/activate`).

| Time | Show | Say / do (exact commands) |
|---|---|---|
| 0:00-0:30 | Repo layout | `ls` and `tree -L 2 -I '.venv|mlruns'`. Name the pieces: `src/`, `test/`, `k8s/`, `Dockerfile`, `.github/workflows/ci.yml`, `notebooks/`, `docs/`. |
| 0:30-1:15 | Data and EDA | `python -m src.download_data` then `python -m src.eda`. Open `screenshots/eda/`. Mention 303 rows, 164 healthy vs 139 disease, and that cp=4 and thal=7 are strong signals. |
| 1:15-2:30 | Training and MLflow | `python -m src.train`. Then `MLFLOW_ALLOW_FILE_STORE=true mlflow ui --port 5000`. Show the runs list, compare runs, open best run `logreg-C0.3` (params, metrics, ROC artifact) and the registry entry `heart-disease-classifier` v2. Stop the UI. |
| 2:30-3:00 | Tests and lint | `pytest test -v` (18 pass) and `flake8 src test` (clean). |
| 3:00-3:50 | API | `uvicorn src.api:app --port 8000`. Open http://localhost:8000/docs. In another terminal: `curl localhost:8000/health` and `curl -X POST localhost:8000/predict -H 'Content-Type: application/json' -d '{"age":57,"sex":1,"cp":4,"trestbps":140,"chol":241,"fbs":0,"restecg":0,"thalach":123,"exang":1,"oldpeak":0.2,"slope":2,"ca":0,"thal":7}'` then `curl localhost:8000/metrics`. |
| 3:50-4:25 | Docker | `docker build -t heart-disease-api:latest .`, `docker run -d --name heart-api -p 8000:8000 heart-disease-api:latest`, `scripts/smoke_test.sh http://localhost:8000`, `docker rm -f heart-api`. |
| 4:25-5:15 | Kubernetes and monitoring | `scripts/deploy_local.sh`, `kubectl -n heart-mlops get pods,svc,ingress -o wide`, `kubectl -n heart-mlops port-forward svc/heart-api 8000:80` and re-run the smoke test. Then `kubectl -n heart-mlops port-forward svc/grafana 3000:3000`, open http://localhost:3000, dashboard "Heart Disease API". |
| 5:15-5:45 | CI/CD | Show `.github/workflows/ci.yml`, then the GitHub Actions tab with a green `ci` run (lint, test, train, docker build and smoke test). |
| 5:45-6:00 | Wrap-up | Point to `docs/report/MLOps_Assignment1_Report.pdf` and the repo link. |

Tip: send a few `/predict` calls before opening Grafana so the panels have data.
