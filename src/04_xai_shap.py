#!/usr/bin/env python3
"""
Phase 4 — TreeSHAP explainability on alert samples.

Policy:
  - Explain predicted-attack alerts only (not every packet)
  - Primary model: LightGBM multi-class (and binary)
  - Measure explanation latency and save global/local artifacts

Software-only. No hardware.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

ROOT = Path(__file__).resolve().parents[1]
SPLIT_PATH = ROOT / "artifacts" / "processed" / "toniot_network_splits.joblib"
MODEL_DIR = ROOT / "artifacts" / "models"
RESULT_DIR = ROOT / "results"
FIG_DIR = ROOT / "figures"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

N_ALERTS = 200  # local explanations budget
RANDOM_STATE = 42


def load_bundle():
    data = joblib.load(SPLIT_PATH)
    return data


def measure_shap_overhead(explainer, X_alerts: pd.DataFrame, repeats: int = 3):
    # Warm-up
    _ = explainer.shap_values(X_alerts.iloc[: min(10, len(X_alerts))])
    times = []
    shap_out = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        shap_out = explainer.shap_values(X_alerts)
        times.append(time.perf_counter() - t0)
    return shap_out, float(np.mean(times)), float(np.std(times))


def global_importance_from_shap(shap_values, feature_names, class_names=None):
    """Aggregate mean(|SHAP|) into a table."""
    # Binary tree models often return (n, f); multiclass often list/array (c, n, f) or (n, f, c)
    if isinstance(shap_values, list):
        # list of per-class arrays
        mats = [np.abs(sv).mean(axis=0) for sv in shap_values]
        mean_abs = np.mean(np.vstack(mats), axis=0)
        per_class = {
            (class_names[i] if class_names else str(i)): mats[i].tolist()
            for i in range(len(mats))
        }
    else:
        arr = np.array(shap_values)
        if arr.ndim == 2:
            mean_abs = np.abs(arr).mean(axis=0)
            per_class = None
        elif arr.ndim == 3:
            # (n, f, c) or (c, n, f)
            if arr.shape[1] == len(feature_names):
                # (n, f, c)
                mean_abs = np.abs(arr).mean(axis=(0, 2))
                per_class = {
                    (class_names[i] if class_names else str(i)): np.abs(arr[:, :, i]).mean(axis=0).tolist()
                    for i in range(arr.shape[2])
                }
            else:
                # (c, n, f)
                mean_abs = np.abs(arr).mean(axis=(0, 1))
                per_class = {
                    (class_names[i] if class_names else str(i)): np.abs(arr[i]).mean(axis=0).tolist()
                    for i in range(arr.shape[0])
                }
        else:
            raise ValueError(f"Unexpected SHAP shape: {arr.shape}")

    order = np.argsort(mean_abs)[::-1]
    table = pd.DataFrame(
        {
            "feature": [feature_names[i] for i in order],
            "mean_abs_shap": mean_abs[order],
        }
    )
    return table, per_class


def run_for_model(task: str, model_path: Path, data, binary: bool):
    print(f"\n=== XAI: {task} / {model_path.name} ===")
    model = joblib.load(model_path)
    X_test = data["X_test"]
    feature_names = data["feature_names"]
    class_names = data.get("class_names")

    if binary:
        y_true = data["y_bin_test"]
        y_pred = model.predict(X_test)
        alert_idx = np.where(y_pred == 1)[0]
    else:
        y_true = data["y_multi_test"]
        y_pred = model.predict(X_test)
        # Alerts = anything predicted not normal
        normal_id = list(class_names).index("normal")
        alert_idx = np.where(y_pred != normal_id)[0]

    rng = np.random.default_rng(RANDOM_STATE)
    if len(alert_idx) == 0:
        raise RuntimeError(f"No alerts found for {task}")

    sample_n = min(N_ALERTS, len(alert_idx))
    chosen = rng.choice(alert_idx, size=sample_n, replace=False)
    # Ensure DataFrame with feature names for SHAP plotting / consistency
    if not isinstance(X_test, pd.DataFrame):
        X_test = pd.DataFrame(X_test, columns=feature_names)
    X_alerts = X_test.iloc[chosen]

    # Fast TreeSHAP (path-dependent). Avoid interventional+background here:
    # it is far too slow for multiclass LightGBM in this pipeline.
    explainer = shap.TreeExplainer(model, feature_perturbation="tree_path_dependent")
    shap_values, mean_t, std_t = measure_shap_overhead(explainer, X_alerts)

    ms_per_alert = (mean_t / sample_n) * 1000.0
    table, per_class = global_importance_from_shap(
        shap_values, feature_names, None if binary else class_names
    )

    prefix = f"{task}_lightgbm"
    table_path = RESULT_DIR / f"xai_global_importance_{prefix}.csv"
    table.to_csv(table_path, index=False)

    # Global bar plot
    top = table.head(15)
    plt.figure(figsize=(8, 5))
    plt.barh(top["feature"][::-1], top["mean_abs_shap"][::-1], color="#1f4e79")
    plt.xlabel("mean(|SHAP|)")
    plt.title(f"TreeSHAP global importance — {task} LightGBM (top 15)")
    plt.tight_layout()
    fig_path = FIG_DIR / f"shap_global_{prefix}.png"
    plt.savefig(fig_path, dpi=150)
    plt.close()

    # Save one local explanation example (top alert by model confidence if available)
    example = {
        "n_alerts_available": int(len(alert_idx)),
        "n_alerts_explained": int(sample_n),
        "alert_indices_sample": chosen[:10].tolist(),
        "top_features_global": table.head(10).to_dict(orient="records"),
    }
    if per_class is not None:
        # store only top-5 features per class to keep file small
        compact = {}
        for cls, vals in per_class.items():
            order = np.argsort(vals)[::-1][:5]
            compact[cls] = [
                {"feature": feature_names[i], "mean_abs_shap": float(vals[i])} for i in order
            ]
        example["per_class_top5"] = compact

    overhead = {
        "task": task,
        "model": "LightGBM",
        "n_alerts_explained": sample_n,
        "shap_seconds_mean": round(mean_t, 4),
        "shap_seconds_std": round(std_t, 4),
        "ms_per_alert": round(ms_per_alert, 4),
        "feature_perturbation": "tree_path_dependent",
    }

    return overhead, example, table_path, fig_path


def main():
    data = load_bundle()
    overhead_rows = []
    details = {}

    bin_model = MODEL_DIR / "binary_lightgbm.joblib"
    multi_model = MODEL_DIR / "multiclass_lightgbm.joblib"

    for task, path, binary in [
        ("binary", bin_model, True),
        ("multiclass", multi_model, False),
    ]:
        overhead, example, table_path, fig_path = run_for_model(task, path, data, binary)
        overhead_rows.append(overhead)
        details[task] = {
            "example": example,
            "global_importance_csv": str(table_path),
            "figure": str(fig_path),
        }
        print(json.dumps(overhead, indent=2))

    oh_df = pd.DataFrame(overhead_rows)
    oh_path = RESULT_DIR / "xai_overhead.csv"
    oh_df.to_csv(oh_path, index=False)
    (RESULT_DIR / "xai_details.json").write_text(json.dumps(details, indent=2))

    print("\n=== Phase 4 complete ===")
    print(f"Overhead: {oh_path}")
    print(f"Details:  {RESULT_DIR / 'xai_details.json'}")
    print(f"Figures:  {FIG_DIR}")


if __name__ == "__main__":
    main()
