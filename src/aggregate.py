#!/usr/bin/env python3
"""Aggregate multi-seed runs into per-dataset findings (mean +/- sd + range).

Reads results/runs.csv and results/<dataset>/seed_<s>/seed_metrics.json.
Writes results/<dataset>/findings.json, results/findings_all.json and
results/MULTISEED_SUMMARY.md. No significance tests at n=3.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
METRICS = [
    "accuracy", "precision", "recall", "f1", "macro_f1", "weighted_f1",
    "train_seconds", "infer_ms_per_sample", "model_size_mb",
]


def _stat(values: dict[int, float]) -> dict:
    arr = np.array(list(values.values()), dtype=float)
    return {
        "mean": round(float(arr.mean()), 6),
        "sd": round(float(arr.std(ddof=1)) if len(arr) > 1 else 0.0, 6),
        "min": round(float(arr.min()), 6),
        "max": round(float(arr.max()), 6),
        "by_seed": {str(k): round(float(v), 6) for k, v in sorted(values.items())},
    }


def main() -> None:
    runs_path = ROOT / "results" / "runs.csv"
    if not runs_path.exists():
        raise SystemExit(f"Missing {runs_path}; run src/run_dataset.py first.")

    runs = pd.read_csv(runs_path)
    all_findings = {}
    md = [
        "# Multi-seed findings",
        "",
        "n=3 seeds: mean +/- sd (min-max). Cross-dataset macro-F1 is descriptive, not a head-to-head test.",
        "",
    ]

    for dataset, group in runs.groupby("dataset", sort=True):
        dataset_dir = ROOT / "results" / dataset
        dataset_dir.mkdir(parents=True, exist_ok=True)
        seeds = sorted(int(s) for s in group["seed"].unique())

        seed_details = {}
        for s in seeds:
            p = dataset_dir / f"seed_{s}" / "seed_metrics.json"
            if p.exists():
                seed_details[s] = json.loads(p.read_text())

        by_task_model = {}
        for (task, model), gg in group.groupby(["task", "model"], sort=True):
            entry = {"n_seeds": len(gg)}
            for metric in METRICS:
                vals = {
                    int(row["seed"]): float(row[metric])
                    for _, row in gg.iterrows()
                }
                entry[metric] = _stat(vals)

            # Per-class f1 across seeds (classes present in every seed).
            per_class = {}
            seed_classes = {}
            for s, detail in sorted(seed_details.items()):
                task_key = task if task in detail.get("models", {}) else None
                if task_key is None:
                    continue
                rep = detail["models"][task_key].get(model, {}).get("per_class", {})
                for cls, vals in rep.items():
                    if not isinstance(vals, dict) or "f1-score" not in vals:
                        continue
                    per_class.setdefault(cls, {})[s] = float(vals["f1-score"])
                seed_classes[s] = {
                    cls for cls, vals in rep.items()
                    if isinstance(vals, dict) and "f1-score" in vals
                }
            common = set.intersection(*seed_classes.values()) if seed_classes else set()
            entry["per_class_f1"] = {
                cls: _stat(per_class[cls]) for cls in sorted(common)
            }

            # XAI cost (LightGBM only).
            xai_vals = {}
            if model == "LightGBM":  # TreeSHAP was only run on LightGBM models
                for s, detail in sorted(seed_details.items()):
                    task_key = task if task in detail.get("xai", {}) else None
                    if task_key is None:
                        continue
                    x = detail["xai"][task_key]
                    if x.get("ms_per_alert") is not None:
                        xai_vals[s] = float(x["ms_per_alert"])
            if xai_vals:
                entry["ms_per_alert"] = _stat(xai_vals)

            by_task_model[f"{task}/{model}"] = entry

        findings = {
            "dataset": dataset,
            "seeds": seeds,
            "n_seeds": len(seeds),
            "note": "mean +/- sd and range over seeds; no significance tests at n=3",
            "by_task_model": by_task_model,
        }
        (dataset_dir / "findings.json").write_text(json.dumps(findings, indent=2), encoding="utf-8")
        all_findings[dataset] = findings

        md.append(f"## {dataset}")
        md.append("")
        md.append(f"Seeds: {', '.join(str(s) for s in seeds)}")
        md.append("")
        md.append("| task/model | macro-F1 (mean±sd) | F1 | size MB | infer ms | SHAP ms/alert |")
        md.append("|---|---|---|---|---|---|")
        for key, e in by_task_model.items():
            mf = e["macro_f1"]
            f1 = e["f1"]
            sz = e["model_size_mb"]
            inf = e["infer_ms_per_sample"]
            sh = e.get("ms_per_alert", {})
            sh_txt = f"{sh['mean']:.2f}±{sh['sd']:.2f}" if sh else "n/a"
            md.append(
                f"| {key} | {mf['mean']:.4f}±{mf['sd']:.4f} | "
                f"{f1['mean']:.4f}±{f1['sd']:.4f} | {sz['mean']:.1f} | "
                f"{inf['mean']:.4f} | {sh_txt} |"
            )
        md.append("")

    (ROOT / "results" / "findings_all.json").write_text(json.dumps(all_findings, indent=2), encoding="utf-8")
    (ROOT / "results" / "MULTISEED_SUMMARY.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote findings for {len(all_findings)} dataset(s): {sorted(all_findings)}")


if __name__ == "__main__":
    main()
