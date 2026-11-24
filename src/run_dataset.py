#!/usr/bin/env python3
"""Run one dataset at one seed: preprocess -> IDS -> TreeSHAP -> ledgers.

Usage:
    python src/run_dataset.py --dataset ton_iot --seed 42

A master seed drives both the stratified 80/20 split and every model's
random_state. All outputs are seed-scoped; nothing from another seed is
overwritten. Every model run is appended (upserted by run_id) to
results/runs.csv.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Determinism must be set before heavy numeric libs are imported where possible.
os.environ.setdefault("PYTHONHASHSEED", "0")
os.environ.setdefault("OMP_NUM_THREADS", "8")

import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

from adapters import get_adapter  # noqa: E402
import harness as H  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="ton_iot | unsw_nb15 | edge_iiot")
    ap.add_argument("--seed", required=True, type=int, help="master seed (e.g. 42)")
    ap.add_argument("--skip-xai", action="store_true", help="skip TreeSHAP (smoke/debug only)")
    args = ap.parse_args()

    seed = int(args.seed)
    np.random.seed(seed)

    adapter = get_adapter(args.dataset)
    missing = adapter.missing_files()
    if missing:
        print(json.dumps({
            "status": "BLOCKED_MISSING_DATA",
            "dataset": adapter.NAME,
            "expected_paths": missing,
        }, indent=2))
        return 2

    t_start = time.perf_counter()
    timestamp = H.utc_now()
    git_commit = H.git_commit()
    cfg = H.canonical_config(adapter, seed)
    cfg_hash = H.sha256_text(json.dumps(cfg, sort_keys=True, default=str))

    H.ensure_preanalysis()

    out_dir = H.ROOT / "results" / adapter.NAME / f"seed_{seed}"
    model_dir = H.ROOT / "artifacts" / "models" / adapter.NAME / f"seed_{seed}"
    proc_dir = H.ROOT / "artifacts" / "processed" / adapter.NAME / f"seed_{seed}"
    for d in (out_dir, model_dir, proc_dir):
        d.mkdir(parents=True, exist_ok=True)

    print(f"\n=== {adapter.DISPLAY} | seed {seed} | config {cfg_hash[:12]} ===", flush=True)

    data = H.prepare_split(adapter, seed)
    data.update({
        "dataset": adapter.NAME,
        "config_hash": cfg_hash,
        "git_commit": git_commit,
        "timestamp": timestamp,
    })

    warnings = H.leakage_sentinel(data)

    rows = []
    details = {}
    models = {}
    for task_key in ("binary", "multiclass"):
        details[task_key] = {}
        for kind in ("rf", "lgbm"):
            model, row, detail = H.train_one(kind, task_key, data, seed, model_dir)
            models[(task_key, kind)] = model
            rows.append(row)
            details[task_key][row["model"]] = detail
            print(
                f"  {task_key:11s} {row['model']:12s} "
                f"macro-F1={row['macro_f1']:.4f} f1={row['f1']:.4f} "
                f"size={row['model_size_mb']:.1f}MB train={row['train_seconds']:.1f}s",
                flush=True,
            )

    xai = {}
    if args.skip_xai:
        xai = {"binary": {"skipped": True}, "multiclass": {"skipped": True}}
    else:
        for task_key in ("binary", "multiclass"):
            model = models[(task_key, "lgbm")]
            xai[task_key] = H.shap_explain(model, data, seed, task_key, out_dir)
            ms = xai[task_key].get("ms_per_alert")
            if ms is not None:
                print(f"  XAI {task_key:11s} {ms:.2f} ms/alert", flush=True)

    seed_metrics = {
        "dataset": adapter.NAME,
        "display": adapter.DISPLAY,
        "seed": seed,
        "timestamp": timestamp,
        "git_commit": git_commit,
        "config_hash": cfg_hash,
        "raw_rows": data["raw_rows"],
        "rows_after_dedup": data["dedup_rows"],
        "duplicates_removed": data["raw_rows"] - data["dedup_rows"],
        "n_train": data["n_train"],
        "n_test": data["n_test"],
        "n_features": len(data["feature_names"]),
        "n_classes": len(data["class_names"]),
        "class_names": data["class_names"],
        "feature_names": data["feature_names"],
        "categorical_features": data["cat_cols"],
        "numeric_features": data["num_cols"],
        "dropped_columns": list(adapter.LAST_DROPPED),
        "leakage_warnings": warnings,
        "models": details,
        "runs": rows,
        "xai": xai,
        "elapsed_seconds": round(time.perf_counter() - t_start, 1),
    }
    metrics_path = out_dir / "seed_metrics.json"
    metrics_path.write_text(json.dumps(seed_metrics, indent=2, default=str))

    H.append_run_rows(rows)
    H.update_registry(adapter, seed_metrics)

    lines = [
        "=" * 72,
        f"{adapter.DISPLAY} | seed {seed} | {timestamp}",
        "=" * 72,
        f"rows: raw={data['raw_rows']:,} dedup={data['dedup_rows']:,} "
        f"(-{data['raw_rows'] - data['dedup_rows']:,}) "
        f"train={data['n_train']:,} test={data['n_test']:,}",
        f"features={len(data['feature_names'])} classes={len(data['class_names'])}",
        "",
    ]
    for row in rows:
        lines.append(
            f"{row['task']:11s} {row['model']:12s} acc={row['accuracy']:.4f} "
            f"macroF1={row['macro_f1']:.4f} f1={row['f1']:.4f} "
            f"size={row['model_size_mb']:.1f}MB infer={row['infer_ms_per_sample']:.4f}ms"
        )
    lines.append("")
    for task_key, info in xai.items():
        lines.append(
            f"XAI {task_key}: {info.get('ms_per_alert')} ms/alert "
            f"({info.get('n_alerts_explained')} alerts)"
        )
    if warnings:
        lines.append("")
        lines.append("LEAKAGE SENTINEL WARNINGS:")
        for w in warnings:
            lines.append(f"  {w['feature']}: AUC={w['auc_vs_binary']}")
    lines.append("")
    lines.append(f"Full detail: {metrics_path}")
    (out_dir / "summary.txt").write_text("\n".join(lines))
    print("\n".join(lines), flush=True)

    print(json.dumps({
        "status": "OK",
        "dataset": adapter.NAME,
        "seed": seed,
        "metrics_file": str(metrics_path),
        "elapsed_seconds": seed_metrics["elapsed_seconds"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
