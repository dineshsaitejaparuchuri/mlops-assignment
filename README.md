# Heart-disease risk prediction: MLOps project

This repository contains an end-to-end machine-learning workflow for the Cleveland subset of the UCI Heart Disease dataset. It covers data cleaning and exploratory analysis, model comparison with cross-validation, MLflow experiment tracking, a FastAPI prediction service, automated tests, Docker packaging, Kubernetes manifests, and Prometheus/Grafana monitoring.

The model is an educational demonstration, not a medical device. Its scores should not be used to diagnose or treat a person.

## Project status

- The project code, report, screenshots, notebooks, deployment manifests, and local run logs are included in this package.
- A fresh local validation run passed all 18 unit tests, compiled the Python source/scripts, parsed all 16 YAML files, and passed a live FastAPI smoke test for `/health`, `/predict`, and `/metrics`. The current environment did not have Flake8 installed, so the hosted workflow will be the next fresh lint run.
- The GitHub-hosted CI workflow passed at commit `1978afe` (run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630)), including an end-to-end Kubernetes Ingress check in a disposable kind cluster using `cloud-provider-kind`.
- The project has no persistent public API URL. Local kind deployment and port-forward evidence are included, and hosted CI verified `/health`, `/predict`, and `/metrics` through the Ingress route in its temporary cluster.
- The assignment video is intentionally left for the student to record.

The report contains the repository URL and student details. See [`docs/UPLOAD_TO_GITHUB.md`](docs/UPLOAD_TO_GITHUB.md) for repository and course-submission guidance.

## Quick start (Windows PowerShell)

Use Python 3.11 and run the commands from the project root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, you can run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in the current terminal and activate the environment again. The cleaned CSV is included, so downloading the data is optional for a first run.

```powershell
python -m pytest test -v
python -m src.eda
python -m src.train
uvicorn src.api:app --port 8000
```

Open `http://localhost:8000/docs` to try the API. In another terminal, call `GET /health`, `POST /predict`, and `GET /metrics`. The `/predict` endpoint accepts the 13 input features as JSON and returns the predicted class, label, confidence, and disease probability.

For notebook and report regeneration, install the optional dependencies:

```powershell
pip install -r requirements-notebooks.txt
python scripts/build_notebooks.py
python scripts/build_report.py
```

## Docker

Install and start Docker Desktop, then run:

```powershell
docker build -t heart-disease-api:latest .
docker run --rm -p 8000:8000 heart-disease-api:latest
```

In a second PowerShell terminal, check the container and make a prediction:

```powershell
Invoke-RestMethod http://localhost:8000/health
$body = @{ age=57; sex=1; cp=4; trestbps=140; chol=241; fbs=0; restecg=0; thalach=123; exang=1; oldpeak=0.2; slope=2; ca=0; thal=7 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/predict -ContentType 'application/json' -Body $body
Invoke-RestMethod http://localhost:8000/metrics
```

For Compose, run `docker compose up --build`.

## Kubernetes and monitoring

The `k8s/` folder contains the namespace, Deployment, Service, NodePort, Ingress, and monitoring manifests. Local deployment instructions are in [`scripts/deploy_local.sh`](scripts/deploy_local.sh) (run it in Git Bash or WSL on Windows). The classless Ingress is for kind with the Kubernetes SIG Network `cloud-provider-kind` provider (v0.9.0 or newer); the project avoids [Ingress NGINX, retired in March 2026](https://kubernetes.io/blog/2026/03/30/kubernetes-v1-36-sneak-peek/). Without a provider, use the documented port-forward path. The Prometheus and Grafana configuration lives under `monitoring/` and `k8s/monitoring/`.

## Repository map

- `data/`: cleaned dataset.
- `src/`: download/cleaning, EDA, feature pipeline, training, schemas, and API.
- `notebooks/`: EDA, model training, and inference notebooks.
- `models/`: serialized pipeline and metric summary.
- `test/`: unit tests for preprocessing and API behaviour.
- `.github/workflows/ci.yml`: lint, tests, retraining, Docker build/smoke test, and artifacts.
- `k8s/`, `monitoring/`: deployment and monitoring resources.
- `screenshots/`: EDA charts and captured evidence from local runs.
- `docs/report/MLOps_Assignment1_Report.pdf`: written report (10-page limit targeted).
- `docs/experiments.md`, `docs/run_outputs/`: model comparison and captured run logs.
- `docs/SUBMISSION_CHECKLIST.md`: rubric-by-rubric status and external actions remaining.
- `docs/UPLOAD_TO_GITHUB.md`, `scripts/publish_to_github.ps1`: collect student details, rebuild the report with the remote URL, create the remote repository, and push from Windows.
- `docs/demo_video_script.md`: outline for the video; no video file is included.

## Reproducing the experiment

The training script compares three Logistic Regression settings and six Random Forest settings using stratified five-fold cross-validation. It ranks models by mean cross-validation ROC-AUC, registers the selected run in MLflow, and writes `models/model.joblib` plus `models/metrics.json`. It also saves a summary in `docs/experiments.md` so report metrics can be reviewed without the local `mlruns/` folder.

To start the local MLflow UI, use:

```powershell
$env:MLFLOW_ALLOW_FILE_STORE = "true"
mlflow ui --port 5000
```

## Caveats

The dataset is small and historical, and the reported results come from one held-out split. This project demonstrates a reproducible software workflow; it does not establish clinical validity. The report includes the student details and repository URL. GitHub Actions verifies the CI pipeline; the kind Ingress test runs in a disposable CI cluster and does not create a persistent public endpoint. The course portal upload and video recording remain outside this repository; the video is intentionally omitted at the student's request.
