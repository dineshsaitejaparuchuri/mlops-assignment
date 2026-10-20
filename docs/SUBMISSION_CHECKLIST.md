# Assignment 1 requirement-to-evidence crosswalk

I used this checklist to locate evidence for each requirement in the assignment brief. It is a navigation aid, not a self-assigned grade; the instructor determines how the work is assessed.

| Rubric area | Marks | Evidence included | Notes / remaining action |
|---|---:|---|---|
| Data acquisition and EDA | 5 | `src/download_data.py`, `data/heart_cleaned.csv`, `src/eda.py`, `notebooks/01_eda.ipynb`, `screenshots/eda/` | The download script reads the UCI Cleveland source, changes `?` to missing values, converts the target to 0/1, and writes the cleaned CSV. |
| Feature engineering and model development | 8 | `src/features.py`, `src/train.py`, `notebooks/02_training.ipynb`, `docs/experiments.md`, `models/metrics.json` | Nine configurations (three Logistic Regression and six Random Forest) are compared with stratified five-fold CV; selection uses mean ROC-AUC. |
| Experiment tracking | 5 | `src/train.py`, `screenshots/mlflow_*.png`, `docs/experiments.md` | Training logs parameters, metrics, plots, and artifacts to MLflow. A fresh run regenerates the local `mlruns/` store. |
| Model packaging and reproducibility | 7 | `models/model.joblib`, `requirements.txt`, `requirements-notebooks.txt`, `src/features.py` | The saved artifact is a fitted preprocessing-and-model pipeline; training uses a fixed seed and the cleaned dataset is included. |
| CI/CD and automated testing | 8 | `test/`, `.github/workflows/ci.yml`, hosted Actions run [#10](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39402219483) | Run #10 passed lint, tests, training, Docker build/smoke test, and a temporary kind Ingress check. |
| Docker containerization | 5 | `Dockerfile`, Compose file, `src/api.py`, `src/schemas.py`, `screenshots/docker_build_run.png` | The included capture documents a local Docker run; hosted CI also builds and smoke-tests the image. |
| Production deployment | 7 | `k8s/`, `scripts/deploy_local.sh`, `scripts/test_kind_ingress.sh`, `screenshots/k8s_*.png`, `screenshots/ci_ingress_verification.png` | Local screenshots document kind deployment and port-forward access. Hosted run #10 verified the temporary Ingress route. Neither constitutes a persistent public endpoint. |
| Monitoring and logging | 3 | `src/api.py`, `monitoring/`, `k8s/monitoring/`, `screenshots/api_metrics.png`, `screenshots/prometheus_targets.png`, `screenshots/grafana_dashboard.png` | The API emits request logs and Prometheus metrics; Grafana and Prometheus configuration and screenshots are included. |
| Documentation and reporting | 2 | `README.md`, `docs/report/MLOps_Assignment1_Report.pdf`, `docs/report/architecture.png`, `screenshots/` | The report is 10 pages and includes setup, results, architecture, screenshots, and repository details. |

## Point-by-point crosswalk against the assignment PDF

| Assignment requirement | Evidence in this repository | Notes |
|---|---|---|
| Obtain the UCI Heart Disease data and provide a download script or instructions. | `src/download_data.py`, `data/heart_cleaned.csv`, `README.md` | README identifies the Cleveland source and gives the command to regenerate the cleaned CSV. |
| Clean/preprocess data, handle missing values, and encode features. | `src/download_data.py`, `src/features.py`, `test/test_features.py` | `?` is converted to missing values; the fitted pipeline imputes missing values and one-hot encodes categorical features. |
| Include EDA visualizations for distributions, correlations, and class balance. | `src/eda.py`, `notebooks/01_eda.ipynb`, `screenshots/eda/` | The included analysis covers histograms, correlations, class balance, and categorical counts. |
| Prepare final features with scaling and encoding. | `src/features.py`, `notebooks/02_training.ipynb` | Preprocessing includes numeric scaling, categorical encoding, imputation, and engineered `hr_reserve`. |
| Train at least two classifier families and document selection/tuning. | `src/train.py`, `docs/experiments.md`, `models/metrics.json` | Logistic Regression and Random Forest are compared across nine configurations with five-fold CV. |
| Evaluate with cross-validation and accuracy, precision, recall, and ROC-AUC. | `src/train.py`, `docs/experiments.md`, `models/metrics.json` | The experiment record includes those metrics; it also records held-out results. The sample is small, so metrics and threshold behavior are uncertain. |
| Track parameters, metrics, artifacts, and plots for runs. | `src/train.py`, `screenshots/mlflow_*.png`, CI artifact upload | Training logs nine configurations to MLflow; a new run recreates the local store. |
| Save a reusable model, requirements, and preprocessing for reproducibility. | `models/model.joblib`, `requirements.txt`, `requirements-notebooks.txt`, `src/features.py` | The fitted preprocessing pipeline is saved with the model. |
| Unit-test data processing and model/API behavior. | `test/`, hosted Actions run [#10](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39402219483) | Both the local 23-test run and hosted run #10 passed. |
| CI performs linting, tests, model training, and provides artifacts/logs. | `.github/workflows/ci.yml`, hosted Actions run [#10](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39402219483), uploaded workflow artifacts | Run #10 passed lint, tests, training, Docker build and smoke test, Ingress routing, and uploaded run artifacts. |
| Build/run a Docker API; `/predict` accepts JSON and returns a prediction with class probabilities. | `Dockerfile`, `src/api.py`, `src/schemas.py`, `scripts/smoke_test.sh`, `screenshots/docker_build_run.png` | The response fields are `probability_predicted_class` and `probability_disease`; the tuned decision threshold is 0.26. |
| Deploy to cloud or local Kubernetes, expose the service, verify endpoints, and include screenshots. | `k8s/`, `scripts/deploy_local.sh`, `scripts/test_kind_ingress.sh`, `screenshots/k8s_*.png`, `screenshots/ci_ingress_verification.png` | Local deployment is documented through port-forward. Hosted run #10 verified `/health`, `/predict`, and `/metrics` through Ingress in a disposable cluster. I do not claim local Ingress success or a persistent public endpoint. |
| Log API requests and demonstrate monitoring. | `src/api.py`, `monitoring/`, `k8s/monitoring/`, `screenshots/api_metrics.png`, `screenshots/prometheus_targets.png`, `screenshots/grafana_dashboard.png` | Request logs, Prometheus metrics/configuration, Grafana dashboard configuration, and screenshots are included. |
| Submit a report with setup, EDA/model choices, tracking summary, architecture, CI/deployment screenshots, and repository link. | `docs/report/MLOps_Assignment1_Report.pdf`, `docs/report/architecture.png`, `screenshots/` | The report is 10 pages. |
| Include code, Dockerfile, requirements, cleaned data, notebooks, tests, workflow, manifests, and screenshots. | Repository root plus `src/`, `data/`, `notebooks/`, `test/`, `.github/`, `k8s/`, `screenshots/` | The referenced project files are included in the repository. |
| Provide a public API URL if deployed publicly, otherwise local access instructions. | `README.md`, `scripts/deploy_local.sh`, report Section 10 | No persistent public endpoint is configured. The README gives local port-forward commands for the API and monitoring UIs. |
| Provide clean setup from requirements, isolated Docker proof, failure propagation, and clear logs. | `requirements.txt`, `Dockerfile`, `.github/workflows/ci.yml`, uploaded CI artifacts | Hosted run #10 passed and uploaded artifacts/logs. |

## Remaining submission actions

1. Upload the project and report through the course submission page.
2. Review the work and make sure I can explain the implementation and reported results.

The code and documentation are pushed to the GitHub repository. The hosted Ingress evidence is from a temporary CI cluster; the local instructions use port-forwarding and make no claim of a local Ingress route.
