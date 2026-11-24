# Research Pipeline (Software-Only)

**Title:** Resource-Aware Explainable Machine Learning for Post-Quantum-Secured IoT Intrusion Detection  
**Supervisor decision:** Skip hardware integration (no Raspberry Pi / ESP32 deployment)  
**Datasets:** ToN-IoT Network (primary), UNSW-NB15, Edge-IIoTset  
**Protocol:** 3 seeds `{42, 123, 2024}` × 3 datasets = **9 runs completed**

---

## Architecture (three planes)

```
[ToN-IoT / UNSW-NB15 / Edge-IIoTset]
        |
        v
 Adapter + raw dedupe + leakage drops + stratified 80/20 (seeded)
        |
        v
 +------------------+     +------------------+     +------------------+
 | Plane A: IDS     |     | Plane B: XAI     |     | Plane C: PQC     |
 | LightGBM + RF    | --> | TreeSHAP alerts  |     | ML-KEM / ML-DSA  |
 | detect attacks   |     | explain decisions|     | software timing  |
 +------------------+     +------------------+     +------------------+
        |
        v
 Joint report: detection quality + explanation cost + crypto overhead
 (mean ± sd over seeds; results/MULTISEED_SUMMARY.md)
```

---

## Phase status

| Phase | Status | Deliverable |
|---|---|---|
| 0 Setup | Done | `.venv`, deps |
| 1 Dataset audit | Done | `datasets/ToN_IoT/dataset_audit_report.txt`, `datasets/registry.json` |
| 2–4 Multi-seed IDS+XAI | Done | `src/run_dataset.py`, `results/runs.csv`, per-seed metrics |
| 5 PQC software benches | Done (earlier; not re-run) | `results/pqc_benchmarks.csv` |
| 6 Joint analysis | Done | `results/joint_results_snapshot.txt`, `MULTISEED_SUMMARY.md` |
| 7 Writing | In progress | `docs/Paper_Outline_Draft.md` |

---

## Reproduce multi-seed runs

See `MULTISEED_RUNBOOK.md`.

```bash
export PYTHONHASHSEED=0
python src/run_dataset.py --dataset ton_iot   --seed 42
# ... remaining 8 dataset-seed pairs ...
python src/aggregate.py
```

Legacy single-seed scripts (`src/02_preprocess.py` … `05_pqc_benchmark.py`) are retained for reference only.

---

## Headline numbers (n=3; mean ± sd)

| Dataset | Multi LGBM macro-F1 | Binary LGBM F1 | Multi SHAP ms/alert |
|---|---|---|---|
| ToN-IoT | 0.9546±0.0018 | 0.9986±0.0001 | 28.69±3.29 |
| UNSW-NB15 | 0.5912±0.0114 | 0.9580±0.0011 | 41.66±0.59 |
| Edge-IIoTset | 0.8314±0.0022 | 0.9699±0.0006 | 23.80±0.59 |

PQC (host PC): ML-KEM-512 < 0.1 ms/op; ML-DSA-44 sign ≈ 6.9 ms.

---

## Folder structure

```
Research with Ahasan Sir/
├── datasets/
│   ├── ToN_IoT/
│   ├── registry.json
│   ├── UNSW_NB15/          # local only (gitignored)
│   └── Edge_IIoTset/       # local only (gitignored)
├── src/
│   ├── run_dataset.py      # multi-seed entrypoint
│   ├── harness.py
│   ├── aggregate.py
│   ├── adapters/
│   ├── 02_preprocess.py    # legacy
│   ├── 03_train_ids.py     # legacy
│   ├── 04_xai_shap.py      # legacy
│   └── 05_pqc_benchmark.py # legacy
├── artifacts/
├── results/
├── figures/
├── docs/
├── MULTISEED_RUNBOOK.md
└── writing/preanalysis.json
```

---

## What NOT to do

- Do not implement ESP32 / Raspberry Pi code
- Do not claim first PQC+XAI+IDS paper
- Do not say XAI replaces deep learning
- Do not keep IP/port features in the main model
- Do not report accuracy alone under imbalance
- Do not treat cross-dataset macro-F1 as a significance test at n=3

---

## Immediate next action

**Write the Results section from `results/MULTISEED_SUMMARY.md` and refresh manuscript figures to match multi-seed timings.**
