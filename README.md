# Heart-disease risk prediction: MLOps project

I built this project around the Cleveland subset of the UCI Heart Disease dataset. It includes data preparation and exploration, model comparison, MLflow experiment tracking, a FastAPI prediction service, automated tests, Docker packaging, Kubernetes manifests, and Prometheus/Grafana monitoring.

This model is an educational demonstration, not a medical device. Its predictions should not be used to diagnose or treat anyone.

## Data and target

The download script reads the processed Cleveland file from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data), with an official UCI archive fallback. It converts `?` entries to missing values, converts columns to numeric types, and maps the original target values 0–4 to a binary target: 0 means no recorded disease, and values 1–4 become 1 (disease present). The source has 303 rows; six values are missing (four in `ca`, two in `thal`). The cleaned file keeps those NaNs intentionally; the pipeline imputes them inside each training fold to avoid leakage. The maximum cholesterol value is 564 mg/dl; I retain it and discuss it as an extreme observation rather than dropping it without evidence. The cleaned file is included, so downloading it again is optional.

To download and regenerate the cleaned CSV:

```bash
python -m src.download_data
```

## Setup and quick start

The CI workflow and Docker image use Python 3.11. Local Windows verification was run with Python 3.12.10. These commands work in a POSIX shell on Linux/macOS:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest test -v
python -m src.eda
python -m src.train
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

On Windows PowerShell, create and activate the environment with `py -3.11 -m venv .venv` and `.\.venv\Scripts\Activate.ps1`, then install requirements as above. If activation is blocked, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again.

Open `http://localhost:8000/docs` to try the API. `GET /health`, `POST /predict`, and `GET /metrics` are also available. The response includes the predicted class, label, `probability_predicted_class`, and `probability_disease`. The tuned 0.26 threshold favors recall, so the predicted class may be disease even when its class probability is below 0.5; `probability_predicted_class` names this value without implying a 0.5 cutoff.

For notebook execution, install the optional dependencies:

```bash
pip install -r requirements-notebooks.txt
python scripts/build_notebooks.py
```

## Model and results

I compared three Logistic Regression settings with six Random Forest settings using stratified five-fold cross-validation on the training split. Logistic Regression with `C=0.3` had the highest mean CV ROC-AUC (0.904) and was selected; model selection and the reported CV summary use the same folds, so the CV scores are not an unbiased post-selection estimate. The held-out split contains 61 records; at the default 0.5 threshold its accuracy was 0.902, precision 0.867, recall 0.929, and ROC-AUC 0.970. A threshold of 0.26, selected from out-of-fold training predictions to target at least 90% recall, yielded held-out accuracy 0.836, precision 0.737, recall 1.000, and ROC-AUC 0.970. The lower threshold prioritizes missed cases over extra follow-up and increases false positives. `hr_reserve` has target correlation -0.359, weaker than raw `thalach` (-0.417); I retained it as a small feature-engineering ablation rather than claiming a stronger linear signal. These estimates are uncertain because the dataset and test split are small; this is not a clinically validated operating point. See [`docs/experiments.md`](docs/experiments.md) for the full comparison and caveats.

## Docker

With Docker installed and running:

```bash
docker build -t heart-disease-api:1.0.0 .
docker run --rm -p 8000:8000 heart-disease-api:1.0.0
```

In another terminal, open `http://localhost:8000/docs`, or send requests to `/health`, `/predict`, and `/metrics`. Compose is also available with `docker compose up --build`.

## Local Kubernetes and monitoring

The local deployment script uses Docker plus either kind or minikube, and requires `kubectl`. On Linux/macOS, run:

```bash
bash scripts/deploy_local.sh
```

On Windows, run the script from Git Bash or WSL. The script builds and loads the image, applies the API and monitoring manifests, and waits for the deployments. In separate terminals, use the port forwards printed by the script:

```bash
kubectl -n heart-mlops port-forward svc/heart-api 8000:80
kubectl -n heart-mlops port-forward svc/prometheus 9090:9090
kubectl -n heart-mlops port-forward svc/grafana 3000:3000
```

Then use `http://localhost:8000/docs` for the API, `http://localhost:9090` for Prometheus, and `http://localhost:3000` for Grafana. The deployment script generates a Grafana password Secret and prints the password; set `GRAFANA_ADMIN_PASSWORD` before deployment to supply your own. Compose uses the development default `admin` / `admin`, which can be overridden with `GF_SECURITY_ADMIN_USER` and `GF_SECURITY_ADMIN_PASSWORD`. The Ingress manifest is applied locally, but local routing requires kind with `cloud-provider-kind` configured. Add `<ingress-address> heart.local` to the hosts file (`C:\Windows\System32\drivers\etc\hosts` on Windows or `/etc/hosts` on Linux/macOS), then run `curl -H 'Host: heart.local' http://<ingress-address>/health`. Local Ingress routing is not claimed as verified here. GitHub Actions verified the route in its disposable CI cluster; no persistent public endpoint is configured.

## Repository map

- `data/`: included cleaned Cleveland dataset.
- `src/download_data.py`: download, missing-value conversion, and binary target creation.
- `src/eda.py`, `notebooks/01_eda.ipynb`, `screenshots/eda/`: exploratory analysis and plots.
- `src/features.py`, `src/train.py`, `notebooks/02_training.ipynb`: feature processing, training, comparison, and model selection.
- `models/`: serialized fitted pipeline and metric summary.
- `src/api.py`, `src/schemas.py`: prediction API and request/response schemas.
- `test/`: preprocessing and API tests.
- `.github/workflows/ci.yml`: lint, tests, training, Docker smoke test, and Kubernetes Ingress verification.
- `k8s/`, `monitoring/`: Kubernetes and Prometheus/Grafana resources.
- `screenshots/`, `docs/run_outputs/`: captured evidence and run logs.
- `docs/experiments.md`: experiment settings, metrics, and threshold caveats.
- `docs/report/MLOps_Assignment1_Report.pdf`: written report.
- `docs/SUBMISSION_CHECKLIST.md`: requirement-to-evidence crosswalk.
- `src/predict.py`: standalone JSON-file inference using the committed model.
- `requirements-serve.txt`: minimal pinned dependencies for the container.
- `docs/EVIDENCE_NOTES.md`: screenshot provenance and evidence limitations.

## Experiment tracking

Training logs parameters, metrics, and artifacts to MLflow and writes `models/model.joblib` and `models/metrics.json`. To open the local MLflow UI after training:

```bash
export MLFLOW_ALLOW_FILE_STORE=true  # PowerShell: $env:MLFLOW_ALLOW_FILE_STORE = "true"
mlflow ui --port 5000
```


The repository includes local run evidence and hosted CI evidence. Terminal PNGs are renderings of saved command output, not desktop terminal screenshots. The GitHub Actions run-summary image is an actual browser capture; the linked run [#10](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39402219483) passed lint, tests, training, Docker build and smoke tests, and the Kubernetes Ingress route check in a temporary cluster. The course portal upload remains an external step.
