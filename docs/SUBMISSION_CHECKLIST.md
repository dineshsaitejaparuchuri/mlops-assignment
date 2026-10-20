# Assignment 1 submission checklist

This checklist maps the current project to the official 50-mark rubric. Status labels reflect the evidence currently in the package; they are not a guarantee of an instructor's grade.

| Rubric item | Marks | Current status | Evidence / remaining action |
|---|---:|---|---|
| Data acquisition and EDA | 5 | Complete in package | `src/download_data.py`, `src/eda.py`, `data/heart_cleaned.csv`, EDA notebook and plots. |
| Feature engineering and model development | 8 | Complete in package | `src/features.py`, `src/train.py`, 9 configurations across Logistic Regression and Random Forest, 5-fold CV, metrics in `models/metrics.json` and `docs/experiments.md`. |
| Experiment tracking | 5 | Complete in package | MLflow integration in `src/train.py`, screenshots of runs/registry/artifacts, committed experiment summary. Local `mlruns/` history itself is generated on a fresh run and is not bundled. |
| Model packaging and reproducibility | 7 | Complete in package | Saved preprocessing-plus-model pipeline in `models/model.joblib`, pinned core dependencies, fixed random seed, included cleaned dataset and download script. |
| CI/CD and automated testing | 8 | Hosted workflow verified | The 18 tests, lint, training, image build, container smoke test, and kind Ingress route check passed in GitHub Actions run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630). |
| Docker containerization | 5 | Implemented; evidence captured | `Dockerfile`, Compose file, `/predict`, `/health`, `/metrics`, and saved successful local build/smoke-test evidence. The API itself passed a fresh live smoke test for `/health`, `/predict`, and `/metrics` using the local Uvicorn server. Docker is unavailable in this environment, so a fresh image build/run could not be repeated here; earlier local Docker evidence is bundled. |
| Production deployment | 7 | Local kind deployment captured; hosted Ingress route verified | Kubernetes manifests and monitoring resources exist. Prior kind evidence shows a live Deployment and API smoke test through port-forward. GitHub Actions run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630) created a disposable kind cluster and verified `/health`, `/predict` and `/metrics` through the classless Ingress using `cloud-provider-kind`. No persistent public API URL is configured. |
| Monitoring and logging | 3 | Complete in package | Request logs, Prometheus metrics, Prometheus config, Grafana dashboard config and captured screenshots. |
| Documentation and reporting | 2 | Complete in package | Rebuilt 10-page PDF includes the repository URL and student name/roll number, along with setup instructions, architecture diagram, screenshots and run outputs. |
| Video recording | Deliverable | Excluded by user request | `docs/demo_video_script.md` is only a script; no video file is included. |

## Final pre-submission actions

1. The final code and documentation are pushed to `main`; the hosted pipeline and Ingress check passed in run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630).
2. The rebuilt report was checked at 10 pages and includes the repository URL and student details.
3. Upload the repository and report through the course submission page. The video is intentionally excluded at the student's request.

The report and project intentionally state what has and has not been verified. A temporary CI cluster proves the Kubernetes route test; it is not a persistent public service.
