import json
import os
import tempfile
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mlflow  # noqa: E402
import mlflow.sklearn  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.base import clone  # noqa: E402
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (ConfusionMatrixDisplay, RocCurveDisplay,  # noqa: E402
                             accuracy_score, precision_score, recall_score,
                             roc_auc_score)
from sklearn.model_selection import (ParameterGrid, StratifiedKFold,  # noqa: E402
                                     cross_val_predict, cross_validate,
                                     train_test_split)

from src.features import RAW_FEATURES, build_pipeline  # noqa: E402

os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")  # file store is opt-in in MLflow 3.17

SEED = 42
DATA = Path("data/heart_cleaned.csv")
MODEL_PATH = Path("models/model.joblib")
METRICS_PATH = Path("models/metrics.json")
EXPERIMENTS_MD = Path("docs/experiments.md")
EXPERIMENT_NAME = "heart-disease-risk"
REGISTERED_NAME = "heart-disease-classifier"
TARGET_RECALL = 0.90
SCORING = ["accuracy", "precision", "recall", "roc_auc"]

GRIDS = {
    "logreg": (LogisticRegression(max_iter=2000, random_state=SEED),
               {"C": [0.03, 0.3, 3.0]}),
    "random_forest": (RandomForestClassifier(n_estimators=300, random_state=SEED),
                      {"max_depth": [3, 6, None], "min_samples_leaf": [1, 4]}),
}


def holdout_metrics(y_true, proba, threshold: float) -> dict:
    pred = (proba >= threshold).astype(int)
    return {"accuracy": accuracy_score(y_true, pred),
            "precision": precision_score(y_true, pred, zero_division=0),
            "recall": recall_score(y_true, pred),
            "roc_auc": roc_auc_score(y_true, proba)}


def pick_threshold(y_true, proba) -> float:
    """Highest threshold whose out-of-fold recall still reaches TARGET_RECALL."""
    best = 0.5
    for t in np.arange(0.20, 0.71, 0.01):
        if recall_score(y_true, (proba >= t).astype(int)) >= TARGET_RECALL:
            best = float(round(t, 2))
    return best


def log_plots(pipeline, X_test, y_test) -> None:
    with tempfile.TemporaryDirectory(dir=".") as tmp:
        fig, ax = plt.subplots(figsize=(4.5, 4))
        ConfusionMatrixDisplay.from_estimator(pipeline, X_test, y_test, ax=ax, cmap="Blues")
        ax.set_title("Confusion matrix (test, t=0.5)")
        fig.tight_layout()
        fig.savefig(f"{tmp}/confusion_matrix.png", dpi=130)
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(4.5, 4))
        RocCurveDisplay.from_estimator(pipeline, X_test, y_test, ax=ax)
        ax.plot([0, 1], [0, 1], "--", color="grey")
        ax.set_title("ROC curve (test)")
        fig.tight_layout()
        fig.savefig(f"{tmp}/roc_curve.png", dpi=130)
        plt.close(fig)
        mlflow.log_artifacts(tmp, artifact_path="plots")


def main() -> None:
    df = pd.read_csv(DATA)
    X, y = df[RAW_FEATURES], df["target"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment(EXPERIMENT_NAME)

    results = []
    for name, (estimator, grid) in GRIDS.items():
        for params in ParameterGrid(grid):
            pipe = build_pipeline(clone(estimator).set_params(**params))
            scores = cross_validate(pipe, X_train, y_train, cv=cv, scoring=SCORING)
            cv_metrics = {m: float(scores[f"test_{m}"].mean()) for m in SCORING}
            cv_std = float(scores["test_roc_auc"].std())
            pipe.fit(X_train, y_train)
            proba = pipe.predict_proba(X_test)[:, 1]
            test = holdout_metrics(y_test, proba, 0.5)

            run_label = f"{name}-" + "-".join(f"{k}{v}" for k, v in params.items())
            with mlflow.start_run(run_name=run_label) as run:
                mlflow.log_param("model_type", name)
                mlflow.log_params(params)
                mlflow.log_params({"cv_folds": 5, "seed": SEED, "test_size": 0.2,
                                   "engineered_feature": "hr_reserve"})
                mlflow.log_metrics({f"cv_{k}": v for k, v in cv_metrics.items()})
                fold_metrics = {
                    f"fold_{fold + 1}_{metric}": float(scores[f"test_{metric}"][fold])
                    for metric in SCORING for fold in range(cv.get_n_splits())
                }
                mlflow.log_metrics(fold_metrics)
                mlflow.log_metric("cv_roc_auc_std", cv_std)
                mlflow.log_metrics({f"test_{k}": v for k, v in test.items()})
                mlflow.log_input(mlflow.data.from_pandas(
                    df, source="https://archive.ics.uci.edu/dataset/45/heart",
                    name="heart-disease-cleveland"),
                    context="training")
                mlflow.log_artifact("requirements.txt")
                log_plots(pipe, X_test, y_test)
                model_info = mlflow.sklearn.log_model(
                    pipe, name="model", serialization_format="cloudpickle",
                    input_example=X_train.astype(float).iloc[[0]])
            results.append({"run_id": run.info.run_id, "run_name": run_label,
                            "model_type": name, "params": params, "cv": cv_metrics,
                            "cv_roc_auc_std": cv_std, "test": test, "pipeline": pipe,
                            "estimator": estimator, "model_id": model_info.model_id})
            print(f"{run_label}: cv_auc={cv_metrics['roc_auc']:.4f} "
                  f"test_auc={test['roc_auc']:.4f}")

    best = max(results, key=lambda r: r["cv"]["roc_auc"])
    oof = cross_val_predict(clone(best["pipeline"]), X_train, y_train, cv=cv,
                            method="predict_proba")[:, 1]
    threshold = pick_threshold(y_train, oof)
    test_at_threshold = holdout_metrics(
        y_test, best["pipeline"].predict_proba(X_test)[:, 1], threshold)

    with mlflow.start_run(run_id=best["run_id"]):
        mlflow.log_param("decision_threshold", threshold)
        mlflow.log_metrics({f"test_tuned_{k}": v for k, v in test_at_threshold.items()})
        mlflow.set_tag("selected", "true")
    version = mlflow.register_model(f"models:/{best['model_id']}", REGISTERED_NAME)

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"pipeline": best["pipeline"], "threshold": threshold,
                 "features": RAW_FEATURES}, MODEL_PATH)

    summary = {
        "best_run": best["run_name"], "model_type": best["model_type"],
        "params": best["params"], "decision_threshold": threshold,
        "target_recall": TARGET_RECALL, "mlflow_run_id": best["run_id"],
        "registered_model": {"name": REGISTERED_NAME, "version": str(version.version)},
        "cv_metrics": best["cv"], "test_metrics_at_0.5": best["test"],
        "test_metrics_at_threshold": test_at_threshold,
        "n_train": len(X_train), "n_test": len(X_test),
        "all_runs": [{"run": r["run_name"], "run_id": r["run_id"],
                      "cv_roc_auc": r["cv"]["roc_auc"],
                      "cv_recall": r["cv"]["recall"], "test_roc_auc": r["test"]["roc_auc"]}
                     for r in results],
    }
    METRICS_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_experiments_md(summary, results)
    print(json.dumps({k: summary[k] for k in ("best_run", "decision_threshold", "cv_metrics",
                                              "test_metrics_at_threshold")}, indent=2))


def write_experiments_md(summary: dict, results: list) -> None:
    rows = "\n".join(
        f"| {r['run_name']} | {r['cv']['accuracy']:.3f} | {r['cv']['precision']:.3f} | "
        f"{r['cv']['recall']:.3f} | {r['cv']['roc_auc']:.3f} ± {r['cv_roc_auc_std']:.3f} | "
        f"{r['test']['roc_auc']:.3f} | `{r['run_id']}` |" for r in results)
    cv, t5, tt = (summary["cv_metrics"], summary["test_metrics_at_0.5"],
                  summary["test_metrics_at_threshold"])

    def row(label, m):
        return (f"| threshold {label} | {m['accuracy']:.3f} | {m['precision']:.3f} | "
                f"{m['recall']:.3f} | {m['roc_auc']:.3f} |")

    EXPERIMENTS_MD.parent.mkdir(exist_ok=True)
    EXPERIMENTS_MD.write_text(f"""# Experiment record

Generated by `python -m src.train`; every number below comes from the latest run
(MLflow experiment `{EXPERIMENT_NAME}`, store `./mlruns`).

## Setup
- Data: UCI Cleveland, 303 rows; `?` -> NaN (4 in `ca`, 2 in `thal`);
  target binarised (>0 = disease).
- Split: stratified 80/20 (seed {SEED}); {summary['n_train']} train / {summary['n_test']} test.
  The test set is only used for reporting, never for selection.
- Model selection: stratified 5-fold CV on the training split, ranked by mean ROC-AUC. The
  same folds are used for selection and the reported CV summary; these are not independent
  post-selection performance estimates.
- Preprocessing (inside the saved pipeline, so serving matches training): median + scaling
  for numeric columns; most-frequent imputation + one-hot (unknown ignored) for `cp`,
  `restecg`, `slope`, `thal`, `ca`; most-frequent imputation for binary `sex`, `fbs`,
  `exang`.
- Engineered feature `hr_reserve = thalach / (220 - age)`: the fraction of the age-predicted
  maximum heart rate a patient reached. Raw `thalach` falls with age, so this separates
  "low for their age" from "low because old".

## Search (one MLflow run per configuration, all with plots and CV/test metrics)
Logistic Regression over `C` in {{0.03, 0.3, 3}}; Random Forest (300 trees) over
`max_depth` in {{3, 6, None}} x `min_samples_leaf` in {{1, 4}}. Grids are deliberately small:
with ~240 training rows a large search mostly fits CV noise.

| run | cv acc | cv precision | cv recall | cv ROC-AUC | test ROC-AUC | run id |
|---|---|---|---|---|---|---|
{rows}

## Winner: `{summary['best_run']}`
Chosen for the highest mean CV ROC-AUC ({cv['roc_auc']:.3f}); registered in the MLflow
registry as `{REGISTERED_NAME}` v{summary['registered_model']['version']}.

## Decision threshold chosen for recall
In screening, a missed patient (false negative) costs more than an extra follow-up. The
threshold is the highest value in [0.20, 0.70] whose out-of-fold recall on the training split
is at least {summary['target_recall']:.0%}: **{summary['decision_threshold']}**
(not the default 0.5).
The API applies this threshold to the predicted probability.

| held-out test | accuracy | precision | recall | ROC-AUC |
|---|---|---|---|---|
{row('0.5', t5)}
{row(summary['decision_threshold'], tt)}

Caveat: 61 test rows means each patient moves a metric by ~1.6 points; treat differences
between close configurations as noise.
""", encoding="utf-8")


if __name__ == "__main__":
    main()
