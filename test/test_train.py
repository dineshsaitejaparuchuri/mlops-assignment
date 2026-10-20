import json
from pathlib import Path

import numpy as np

from src.train import holdout_metrics, pick_threshold


def test_pick_threshold_meets_recall_target_without_exceeding_found_bound():
    y = np.array([0, 0, 1, 1, 1])
    probability = np.array([0.05, 0.25, 0.28, 0.55, 0.9])
    threshold = pick_threshold(y, probability)
    assert 0.2 <= threshold <= 0.7
    assert holdout_metrics(y, probability, threshold)["recall"] >= 0.9


def test_committed_metrics_has_reproducible_structure():
    root = Path(__file__).resolve().parents[1]
    summary = json.loads((root / "models" / "metrics.json").read_text(encoding="utf-8"))
    assert summary["best_run"]
    assert 0 < summary["decision_threshold"] < 1
    assert set(summary["cv_metrics"]) == {"accuracy", "precision", "recall", "roc_auc"}
    assert set(summary["test_metrics_at_threshold"]) == {
        "accuracy", "precision", "recall", "roc_auc"}
    assert len(summary["all_runs"]) == 9
    assert all(item.get("run_id") for item in summary["all_runs"])
