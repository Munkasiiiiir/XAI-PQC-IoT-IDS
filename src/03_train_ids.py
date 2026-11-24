#!/usr/bin/env python3
"""
Phase 3 — Train IDS models on processed ToN-IoT Network data.

Models:
  - Random Forest (baseline)
  - LightGBM (primary)

Tasks:
  - Binary classification (label)
  - Multi-class classification (type)

Reports accuracy, precision, recall, F1, macro-F1, per-class metrics,
inference latency, and model size. Software-only (no hardware).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

ROOT = Path(__file__).resolve().parents[1]
SPLIT_PATH = ROOT / "artifacts" / "processed" / "toniot_network_splits.joblib"
MODEL_DIR = ROOT / "artifacts" / "models"
RESULT_DIR = ROOT / "results"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42


def load_data():
    data = joblib.load(SPLIT_PATH)
    return data


def timed_predict(model, X, repeats: int = 5):
    # Warm-up
    _ = model.predict(X[: min(1000, len(X))])
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        pred = model.predict(X)
        times.append(time.perf_counter() - t0)
    return pred, float(np.mean(times)), float(np.std(times))


def model_size_bytes(path: Path) -> int:
    return path.stat().st_size if path.exists() else -1


def evaluate(y_true, y_pred, average_for_binary: bool = True):
    if average_for_binary:
        avg = "binary"
    else:
        avg = "macro"
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average=avg, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average=avg, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, average=avg, zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }


def train_binary(data):
    X_train, X_test = data["X_train"], data["X_test"]
    y_train, y_test = data["y_bin_train"], data["y_bin_test"]

    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=200,
            max_depth=None,
            n_jobs=-1,
            random_state=RANDOM_STATE,
            class_weight="balanced_subsample",
        ),
        "LightGBM": lgb.LGBMClassifier(
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=63,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            class_weight="balanced",
            verbosity=-1,
        ),
    }

    rows = []
    reports = {}

    for name, model in models.items():
        print(f"\n[Binary] Training {name}...")
        t0 = time.perf_counter()
        model.fit(X_train, y_train)
        train_sec = time.perf_counter() - t0

        y_pred, infer_mean, infer_std = timed_predict(model, X_test)
        metrics = evaluate(y_test, y_pred, average_for_binary=True)

        model_path = MODEL_DIR / f"binary_{name.lower()}.joblib"
        joblib.dump(model, model_path)

        row = {
            "task": "binary",
            "model": name,
            "train_seconds": round(train_sec, 3),
            "infer_seconds_mean": round(infer_mean, 4),
            "infer_seconds_std": round(infer_std, 4),
            "infer_ms_per_sample": round(infer_mean / len(X_test) * 1000, 4),
            "model_size_mb": round(model_size_bytes(model_path) / (1024 * 1024), 3),
            **{k: round(v, 4) for k, v in metrics.items()},
        }
        rows.append(row)
        reports[name] = {
            "classification_report": classification_report(y_test, y_pred, digits=4),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        }
        print(json.dumps(row, indent=2))

    return rows, reports


def train_multiclass(data):
    X_train, X_test = data["X_train"], data["X_test"]
    y_train, y_test = data["y_multi_train"], data["y_multi_test"]
    class_names = data["class_names"]

    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=250,
            max_depth=None,
            n_jobs=-1,
            random_state=RANDOM_STATE,
            class_weight="balanced_subsample",
        ),
        "LightGBM": lgb.LGBMClassifier(
            n_estimators=400,
            learning_rate=0.05,
            num_leaves=63,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            class_weight="balanced",
            verbosity=-1,
        ),
    }

    rows = []
    reports = {}

    for name, model in models.items():
        print(f"\n[Multi-class] Training {name}...")
        t0 = time.perf_counter()
        model.fit(X_train, y_train)
        train_sec = time.perf_counter() - t0

        y_pred, infer_mean, infer_std = timed_predict(model, X_test)
        metrics = evaluate(y_test, y_pred, average_for_binary=False)

        model_path = MODEL_DIR / f"multiclass_{name.lower()}.joblib"
        joblib.dump(model, model_path)

        per_class = classification_report(
            y_test,
            y_pred,
            target_names=class_names,
            digits=4,
            output_dict=True,
            zero_division=0,
        )

        row = {
            "task": "multiclass",
            "model": name,
            "train_seconds": round(train_sec, 3),
            "infer_seconds_mean": round(infer_mean, 4),
            "infer_seconds_std": round(infer_std, 4),
            "infer_ms_per_sample": round(infer_mean / len(X_test) * 1000, 4),
            "model_size_mb": round(model_size_bytes(model_path) / (1024 * 1024), 3),
            **{k: round(v, 4) for k, v in metrics.items()},
        }
        rows.append(row)
        reports[name] = {
            "classification_report": classification_report(
                y_test, y_pred, target_names=class_names, digits=4, zero_division=0
            ),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "per_class": per_class,
        }
        print(json.dumps(row, indent=2))

    return rows, reports


def main():
    data = load_data()
    print(
        f"Loaded splits: train={len(data['X_train']):,} test={len(data['X_test']):,} "
        f"features={len(data['feature_names'])}"
    )

    bin_rows, bin_reports = train_binary(data)
    multi_rows, multi_reports = train_multiclass(data)

    metrics_df = pd.DataFrame(bin_rows + multi_rows)
    metrics_path = RESULT_DIR / "ids_metrics.csv"
    metrics_df.to_csv(metrics_path, index=False)

    full_report = {
        "binary": bin_reports,
        "multiclass": multi_reports,
        "feature_names": data["feature_names"],
        "class_names": data["class_names"],
    }
    (RESULT_DIR / "ids_detailed_reports.json").write_text(json.dumps(full_report, indent=2))

    # Human-readable summary
    lines = ["=" * 72, "IDS Training Summary", "=" * 72, metrics_df.to_string(index=False), ""]
    for task, reports in [("Binary", bin_reports), ("Multi-class", multi_reports)]:
        lines.append(f"\n### {task} classification reports")
        for name, rep in reports.items():
            lines.append(f"\n--- {name} ---")
            lines.append(rep["classification_report"])
    summary_path = RESULT_DIR / "ids_summary.txt"
    summary_path.write_text("\n".join(lines))

    print("\n=== Phase 3 complete ===")
    print(f"Metrics: {metrics_path}")
    print(f"Summary: {summary_path}")
    print(f"Models:  {MODEL_DIR}")


if __name__ == "__main__":
    main()
