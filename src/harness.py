"""Shared, deterministic harness for the multi-seed XAI+PQC-IDS runs.

A master seed drives both the stratified 80/20 split and every model's
random_state, so each seed captures data-partition + model-init variance.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
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
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder

ROOT = Path(__file__).resolve().parents[1]

THREADS = 8
TEST_SIZE = 0.20
N_ALERTS = 200
SEEDS = [42, 123, 2024]

LGBM_COMMON = dict(
    learning_rate=0.05,
    num_leaves=63,
    subsample=0.8,
    colsample_bytree=0.8,
    class_weight="balanced",
    verbosity=-1,
    deterministic=True,
    force_row_wise=True,
)

RUN_COLUMNS = [
    "run_id", "dataset", "seed", "task", "model",
    "accuracy", "precision", "recall", "f1", "macro_f1", "weighted_f1",
    "train_seconds", "infer_ms_per_sample", "model_size_mb",
    "n_train", "n_test", "config_hash", "git_commit", "timestamp",
]


# ---------------------------------------------------------------- utilities
def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def versions() -> dict:
    import sklearn

    return {
        "python": sys.version.split()[0],
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "lightgbm": lgb.__version__,
    }


def canonical_config(adapter, seed: int) -> dict:
    return {
        "dataset": adapter.NAME,
        "seed": seed,
        "test_size": TEST_SIZE,
        "threads": THREADS,
        "n_alerts": N_ALERTS,
        "lgbm_common": LGBM_COMMON,
        "rf": {"class_weight": "balanced_subsample", "max_depth": None},
        "estimators": {"rf_binary": 200, "rf_multi": 250, "lgbm_binary": 300, "lgbm_multi": 400},
        "targets": [adapter.TARGET_BINARY, adapter.TARGET_MULTI],
        "versions": versions(),
    }


# ---------------------------------------------------------------- data
def prepare_split(adapter, seed: int) -> dict:
    df = adapter.build_frame()
    # The adapter dedupes RAW rows (placeholders intact) before cleaning and
    # before any columns are dropped. Do NOT dedupe again here: dropping IDs
    # and sparse text after cleaning would merge distinct flows and inflate
    # the duplicate count (the original ToN-IoT policy removes 20,569, not
    # 117,367).
    raw_rows = int(getattr(adapter, "LAST_RAW_ROWS", len(df)))
    dedup_rows = int(getattr(adapter, "LAST_DEDUP_ROWS", len(df)))

    y_bin = df.pop("_y_bin").astype(int).to_numpy()
    y_multi = df.pop("_y_multi").astype(str).reset_index(drop=True)
    X = df

    # Coerce string columns that are actually numeric (Edge-IIoTset especially).
    for c in X.columns:
        if X[c].dtype == bool:
            X[c] = X[c].astype(int)
        elif X[c].dtype == object:
            conv = pd.to_numeric(X[c], errors="coerce")
            non_null = int(X[c].notna().sum())
            if non_null and int(conv.notna().sum()) >= 0.9 * non_null:
                X[c] = conv

    Xtr, Xte, ybtr, ybte, ymtr, ymte = train_test_split(
        X, y_bin, y_multi,
        test_size=TEST_SIZE, random_state=seed, stratify=y_multi,
    )
    Xtr = Xtr.copy()
    Xte = Xte.copy()

    num_cols = [c for c in Xtr.columns if pd.api.types.is_numeric_dtype(Xtr[c])]
    cat_cols = [c for c in Xtr.columns if c not in num_cols]

    if num_cols:
        med = Xtr[num_cols].median().fillna(0)
        Xtr[num_cols] = Xtr[num_cols].fillna(med)
        Xte[num_cols] = Xte[num_cols].fillna(med)

    encoder = None
    if cat_cols:
        for c in cat_cols:
            Xtr[c] = Xtr[c].where(Xtr[c].notna(), "missing").astype(str)
            Xte[c] = Xte[c].where(Xte[c].notna(), "missing").astype(str)
        encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        Xtr[cat_cols] = encoder.fit_transform(Xtr[cat_cols])
        Xte[cat_cols] = encoder.transform(Xte[cat_cols])

    le = LabelEncoder().fit(ymtr)

    return {
        "X_train": Xtr.astype(np.float64),
        "X_test": Xte.astype(np.float64),
        "y_bin_train": ybtr,
        "y_bin_test": ybte,
        "y_multi_train": le.transform(ymtr),
        "y_multi_test": le.transform(ymte),
        "class_names": le.classes_.tolist(),
        "feature_names": Xtr.columns.tolist(),
        "cat_cols": cat_cols,
        "num_cols": num_cols,
        "n_train": int(len(Xtr)),
        "n_test": int(len(Xte)),
        "raw_rows": raw_rows,
        "dedup_rows": dedup_rows,
        "encoder": encoder,
        "label_encoder": le,
    }


def leakage_sentinel(data: dict, top_n: int = 10) -> list[dict]:
    """Flag numeric features whose single-feature AUC vs binary label is ~1."""
    y = np.asarray(data["y_bin_train"])
    X = data["X_train"]
    flags = []
    for c in data["num_cols"]:
        col = X[c].to_numpy()
        if np.nanstd(col) == 0:
            continue
        try:
            auc = float(roc_auc_score(y, col))
        except Exception:
            continue
        if auc > 0.995 or auc < 0.005:
            flags.append({"feature": c, "auc_vs_binary": round(auc, 4)})
    flags.sort(key=lambda d: abs(d["auc_vs_binary"] - 0.5), reverse=True)
    return flags[:top_n]


# ---------------------------------------------------------------- models
def build_model(kind: str, task: str, seed: int):
    if kind == "rf":
        n = 200 if task == "binary" else 250
        return RandomForestClassifier(
            n_estimators=n, max_depth=None, class_weight="balanced_subsample",
            random_state=seed, n_jobs=THREADS,
        )
    n = 300 if task == "binary" else 400
    return lgb.LGBMClassifier(
        n_estimators=n, random_state=seed, n_jobs=THREADS, **LGBM_COMMON
    )


def timed_predict(model, X, repeats: int = 5):
    _ = model.predict(X[: min(1000, len(X))])
    times = []
    pred = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        pred = model.predict(X)
        times.append(time.perf_counter() - t0)
    return pred, float(np.mean(times)), float(np.std(times))


def evaluate(y_true, y_pred, binary: bool) -> dict:
    avg = "binary" if binary else "macro"
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average=avg, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average=avg, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, average=avg, zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }


def train_one(kind: str, task: str, data: dict, seed: int, model_dir: Path):
    model = build_model(kind, task, seed)
    if task == "binary":
        Xtr, Xte = data["X_train"], data["X_test"]
        ytr, yte = data["y_bin_train"], data["y_bin_test"]
        class_names = ["normal", "attack"]
    else:
        Xtr, Xte = data["X_train"], data["X_test"]
        ytr, yte = data["y_multi_train"], data["y_multi_test"]
        class_names = data["class_names"]

    t0 = time.perf_counter()
    model.fit(Xtr, ytr)
    train_sec = time.perf_counter() - t0

    y_pred, infer_mean, infer_std = timed_predict(model, Xte)
    metrics = evaluate(yte, y_pred, binary=(task == "binary"))
    per_class = classification_report(
        yte, y_pred, target_names=class_names, digits=4, output_dict=True, zero_division=0
    )
    cm = confusion_matrix(yte, y_pred).tolist()

    model_name = "RandomForest" if kind == "rf" else "LightGBM"
    path = model_dir / f"{task}_{kind}.joblib"
    joblib.dump(model, path)
    size_mb = path.stat().st_size / (1024 * 1024)
    if kind == "rf":
        # The size is recorded in the ledger, but the file itself is derived
        # data and can reach over 1 GB per seed. Keep LightGBM binaries only.
        path.unlink()

    row = {
        "run_id": f"{data['dataset']}_s{seed}_{task}_{model_name}",
        "dataset": data["dataset"],
        "seed": seed,
        "task": task,
        "model": model_name,
        "accuracy": round(metrics["accuracy"], 4),
        "precision": round(metrics["precision"], 4),
        "recall": round(metrics["recall"], 4),
        "f1": round(metrics["f1"], 4),
        "macro_f1": round(metrics["macro_f1"], 4),
        "weighted_f1": round(metrics["weighted_f1"], 4),
        "train_seconds": round(train_sec, 3),
        "infer_ms_per_sample": round(infer_mean / len(Xte) * 1000, 4),
        "model_size_mb": round(size_mb, 3),
        "n_train": data["n_train"],
        "n_test": data["n_test"],
        "config_hash": data["config_hash"],
        "git_commit": data["git_commit"],
        "timestamp": data["timestamp"],
    }
    detail = {
        "metrics": metrics,
        "per_class": per_class,
        "confusion_matrix": cm,
        "train_seconds": train_sec,
        "infer_seconds_mean": infer_mean,
        "infer_seconds_std": infer_std,
        "model_size_mb": size_mb,
    }
    return model, row, detail


# ---------------------------------------------------------------- XAI
def _global_importance(shap_values, feature_names, class_names=None):
    if isinstance(shap_values, list):
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
            if arr.shape[1] == len(feature_names):
                mean_abs = np.abs(arr).mean(axis=(0, 2))
                per_class = {
                    (class_names[i] if class_names else str(i)): np.abs(arr[:, :, i]).mean(axis=0).tolist()
                    for i in range(arr.shape[2])
                }
            else:
                mean_abs = np.abs(arr).mean(axis=(0, 1))
                per_class = {
                    (class_names[i] if class_names else str(i)): np.abs(arr[i]).mean(axis=0).tolist()
                    for i in range(arr.shape[0])
                }
        else:
            raise ValueError(f"Unexpected SHAP shape: {arr.shape}")

    order = np.argsort(mean_abs)[::-1]
    table = pd.DataFrame({
        "feature": [feature_names[i] for i in order],
        "mean_abs_shap": mean_abs[order],
    })
    return table, per_class


def shap_explain(model, data: dict, seed: int, task: str, out_dir: Path):
    import shap

    X_test = data["X_test"]
    feature_names = data["feature_names"]
    class_names = data["class_names"]

    if task == "binary":
        y_pred = model.predict(X_test)
        alert_idx = np.where(y_pred == 1)[0]
    else:
        y_pred = model.predict(X_test)
        normal_id = list(class_names).index("normal")
        alert_idx = np.where(y_pred != normal_id)[0]

    if len(alert_idx) == 0:
        return {"task": task, "error": "no alerts predicted"}

    rng = np.random.default_rng(seed)
    n = min(N_ALERTS, len(alert_idx))
    chosen = rng.choice(alert_idx, size=n, replace=False)
    X_alerts = X_test.iloc[chosen]

    explainer = shap.TreeExplainer(model, feature_perturbation="tree_path_dependent")
    _ = explainer.shap_values(X_alerts.iloc[: min(10, len(X_alerts))])
    times = []
    sv = None
    for _ in range(3):
        t0 = time.perf_counter()
        sv = explainer.shap_values(X_alerts)
        times.append(time.perf_counter() - t0)

    mean_t = float(np.mean(times))
    std_t = float(np.std(times))
    table, per_class = _global_importance(sv, feature_names, None if task == "binary" else class_names)
    table_path = out_dir / f"xai_global_importance_{task}.csv"
    table.to_csv(table_path, index=False)

    per_class_top5 = None
    if per_class is not None:
        per_class_top5 = {}
        for cls, vals in per_class.items():
            order = np.argsort(vals)[::-1][:5]
            per_class_top5[cls] = [
                {"feature": feature_names[i], "mean_abs_shap": float(vals[i])} for i in order
            ]

    return {
        "task": task,
        "n_alerts_available": int(len(alert_idx)),
        "n_alerts_explained": int(n),
        "shap_seconds_mean": mean_t,
        "shap_seconds_std": std_t,
        "ms_per_alert": mean_t / n * 1000.0,
        "feature_perturbation": "tree_path_dependent",
        "top_features": table.head(10).to_dict(orient="records"),
        "top_features_file": str(table_path),
        "per_class_top5": per_class_top5,
    }


# ---------------------------------------------------------------- ledgers
def append_run_rows(rows: list[dict]) -> Path:
    path = ROOT / "results" / "runs.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new = pd.DataFrame(rows, columns=RUN_COLUMNS)
    if path.exists():
        old = pd.read_csv(path)
        if not old.empty:
            old = old[~old["run_id"].isin(new["run_id"])]
            out = pd.concat([old, new], ignore_index=True)
        else:
            out = new
    else:
        out = new
    out.to_csv(path, index=False)
    return path


def ensure_preanalysis() -> Path:
    path = ROOT / "writing" / "preanalysis.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path
    plan = {
        "created_utc": utc_now(),
        "seeds": SEEDS,
        "seed_semantics": "Each master seed drives BOTH the stratified 80/20 split and every model random_state.",
        "test_size": TEST_SIZE,
        "primary_metric": {"multiclass": "macro_f1", "binary": "f1 (positive class = attack)"},
        "hypotheses": [
            "H1: LightGBM matches or exceeds RandomForest macro-F1 on every dataset.",
            "H2: LightGBM's multi-class model size is much smaller than RandomForest at comparable macro-F1.",
            "H3: Alert-level TreeSHAP cost is driven by class count, not dataset size.",
            "H4: ML-DSA signing dominates the per-alert crypto budget versus ML-KEM and IDS inference.",
        ],
        "falsifiers": [
            "H1 falsified if LightGBM macro-F1 is lower than RF by more than 1 sd on 2+ datasets.",
            "H2 falsified if LightGBM multi-class model is not smaller at equal macro-F1.",
            "H3 falsified if ms/alert does not scale with class count.",
            "H4 falsified if ML-KEM or IDS inference exceeds ML-DSA signing cost.",
        ],
        "comparison_family": "model (RandomForest vs LightGBM) within each dataset and task",
        "multiple_comparison_correction": "none at n=3 seeds; report mean +/- sd and range only, no p-values",
        "frozen_hyperparameters": True,
        "threads": THREADS,
        "n_alerts": N_ALERTS,
        "lgbm_common": LGBM_COMMON,
        "estimators": {"rf_binary": 200, "rf_multi": 250, "lgbm_binary": 300, "lgbm_multi": 400},
    }
    text = json.dumps(plan, indent=2, sort_keys=True)
    plan["plan_sha256"] = sha256_text(text)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True))
    return path


def update_registry(adapter, meta: dict) -> Path:
    path = ROOT / "datasets" / "registry.json"
    if path.exists():
        registry = json.loads(path.read_text())
    else:
        registry = {}
    files = []
    for p in adapter.RAW_FILES:
        if p.exists():
            files.append({
                "path": str(p.relative_to(ROOT)),
                "bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            })
    registry[adapter.NAME] = {
        "display": adapter.DISPLAY,
        "source_url": adapter.SOURCE_URL,
        "license": adapter.LICENSE,
        "targets": {"binary": adapter.TARGET_BINARY, "multi": adapter.TARGET_MULTI},
        "files": files,
        "rows_raw": meta.get("raw_rows"),
        "rows_after_dedup": meta.get("rows_after_dedup"),
        "n_features": meta.get("n_features"),
        "class_names": meta.get("class_names"),
        "dropped_columns": meta.get("dropped_columns"),
        "updated_utc": utc_now(),
    }
    path.write_text(json.dumps(registry, indent=2, sort_keys=True))
    return path
