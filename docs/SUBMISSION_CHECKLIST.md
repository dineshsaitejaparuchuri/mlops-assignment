# Assignment 1 submission checklist

This checklist maps the current project to the official 50-mark rubric. Status labels reflect the evidence currently in the package; they are not a guarantee of an instructor's grade.

| Rubric item | Marks | Current status | Evidence / remaining action |
|---|---:|---|---|
| Data acquisition and EDA | 5 | Complete in package | `src/download_data.py`, `src/eda.py`, `data/heart_cleaned.csv`, EDA notebook and plots. |
| Feature engineering and model development | 8 | Complete in package | `src/features.py`, `src/train.py`, 9 configurations across Logistic Regression and Random Forest, 5-fold CV, metrics in `models/metrics.json` and `docs/experiments.md`. |
| Experiment tracking | 5 | Complete in package | MLflow integration in `src/train.py`, screenshots of runs/registry/artifacts, committed experiment summary. Local `mlruns/` history itself is generated on a fresh run and is not bundled. |
| Model packaging and reproducibility | 7 | Complete in package | Saved preprocessing-plus-model pipeline in `models/model.joblib`, pinned core dependencies, fixed random seed, included cleaned dataset and download script. |
| CI/CD and automated testing | 8 | Partially complete | Workflow and 18 tests are present. Local `act` run is captured, but a GitHub-hosted Actions run must still be triggered after publication. |
| Docker containerization | 5 | Implemented; evidence captured | `Dockerfile`, Compose file, `/predict`, `/health`, `/metrics`, and saved successful local build/smoke-test evidence. The API itself passed a fresh live smoke test for `/health`, `/predict`, and `/metrics` using the local Uvicorn server. Docker is unavailable in this environment, so a fresh image build/run could not be repeated here; earlier local Docker evidence is bundled. |
| Production deployment | 7 | Partially complete | Kubernetes Deployment/Service/NodePort/Ingress manifests and monitoring manifests exist; local kind and port-forward evidence is included. Ingress controller installation and ingress-route verification remain. |
| Monitoring and logging | 3 | Complete in package | Request logs, Prometheus metrics, Prometheus config, Grafana dashboard config and captured screenshots. |
| Documentation and reporting | 2 | Nearly complete | Rebuilt 10-page PDF, setup instructions, architecture diagram, screenshots and run outputs are included. Final GitHub URL and student name/roll number still need to be inserted. |
| Video recording | Deliverable | Excluded by user request | `docs/demo_video_script.md` is only a script; no video file is included. |

## Final pre-submission actions

1. Run `scripts/publish_to_github.ps1` from Windows after installing Git, GitHub CLI and report dependencies. The script prompts for student name, roll number, repository name and visibility; it rebuilds the report with those values before creating and pushing the repository.
2. Open GitHub Actions and confirm the hosted `ci` workflow passes; fix any failures.
3. Install and verify an Ingress controller, or document and verify the exposure method accepted by the instructor.
4. Re-open the generated PDF, confirm the student details and repository URL, and make sure it remains 10 pages.
5. Upload the repository and report through the course submission page. The video remains intentionally excluded from this package.

The report and project intentionally state what has and has not been verified; do not remove those caveats unless the relevant steps are actually completed.
