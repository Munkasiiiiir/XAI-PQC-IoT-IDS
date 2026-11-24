# Resource-Aware Explainable ML for Post-Quantum-Secured IoT Intrusion Detection

Software-only research pipeline extending Sharma & Rani (2025) with:

- **IDS:** LightGBM (primary) + Random Forest (baseline)
- **XAI:** alert-level TreeSHAP
- **PQC:** ML-KEM / ML-DSA software microbenchmarks (host PC)

**Supervisor guidance:** hardware integration (Raspberry Pi / ESP32) skipped.

## Status

Multi-seed cross-dataset benchmark completed (PR #1):

- **3 datasets:** ToN-IoT (primary), UNSW-NB15, Edge-IIoTset
- **3 seeds:** `{42, 123, 2024}` (each seed drives both the 80/20 split and model `random_state`)
- **9 dataset-seed runs** → 36 model rows in `results/runs.csv`
- Statistics: mean ± sd only (no p-values at n=3)

## Repository layout

```
datasets/             # ToN-IoT CSV + registry.json (UNSW/Edge raw CSVs local-only)
src/                  # multi-seed harness + legacy single-seed scripts
artifacts/            # processed splits + models (seed-scoped; mostly gitignored)
results/              # runs.csv, per-dataset findings, PQC benchmarks
figures/              # manuscript figures
docs/                 # paper outline / supervisor memos
MULTISEED_RUNBOOK.md  # how to reproduce the 9 runs
```

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas numpy scikit-learn lightgbm shap matplotlib seaborn joblib pyyaml pqcrypto cryptography python-docx

# Place raw CSVs per MULTISEED_RUNBOOK.md, then:
export PYTHONHASHSEED=0
python src/run_dataset.py --dataset ton_iot   --seed 42
python src/run_dataset.py --dataset ton_iot   --seed 123
python src/run_dataset.py --dataset ton_iot   --seed 2024
python src/run_dataset.py --dataset unsw_nb15 --seed 42
python src/run_dataset.py --dataset unsw_nb15 --seed 123
python src/run_dataset.py --dataset unsw_nb15 --seed 2024
python src/run_dataset.py --dataset edge_iiot --seed 42
python src/run_dataset.py --dataset edge_iiot --seed 123
python src/run_dataset.py --dataset edge_iiot --seed 2024
python src/aggregate.py
```

Legacy single-seed scripts (`src/02_preprocess.py` … `05_pqc_benchmark.py`) remain for reference; prefer the multi-seed harness above.

## Datasets

| Dataset | Role | Dedup rows | Features | Classes |
|---|---|---|---|---|
| ToN-IoT Network | Primary | 190,474 | 30 | 10 |
| UNSW-NB15 | Cross-eval | 257,673 | 42 | 10 |
| Edge-IIoTset (ML CSV) | Cross-eval | 156,986 | 42 | 15 |

Hashes and provenance: `datasets/registry.json`.  
Cite original dataset authors (not Hugging Face mirrors).

## Key results (n=3 seeds, mean ± sd)

**ToN-IoT (primary)**
- Binary LightGBM F1 **0.9986±0.0001**; multi-class macro-F1 **0.9546±0.0018**
- TreeSHAP ≈ **3.35±0.44** ms/alert (binary), **28.69±3.29** ms/alert (multi-class)
- Multi-class LightGBM ≈ **25.5 MB** vs RF ≈ **162.8 MB**

**UNSW-NB15**
- Binary LightGBM F1 **0.9580±0.0011**; multi-class macro-F1 **0.5912±0.0114** (rare classes dominate macro-F1)

**Edge-IIoTset**
- Binary LightGBM F1 **0.9699±0.0006**; multi-class macro-F1 **0.8314±0.0022**
- Binary RF macro-F1 slightly higher than LightGBM (descriptive; H1 soft miss on binary)

**PQC (host PC; not re-run in multi-seed batch)**
- ML-KEM-512 ops < 0.1 ms; ML-DSA-44 sign ≈ **6.9 ms**

Canonical tables: `results/MULTISEED_SUMMARY.md`, `results/runs.csv`, `results/joint_results_snapshot.txt`.

## Notes

- Large model artifacts and UNSW/Edge raw CSVs are gitignored; ToN CSV may use Git LFS.
- This repository does **not** claim to be the first PQC+XAI+IDS system.
- PQC timings are host-PC software benchmarks only (not edge hardware).
- Cross-dataset macro-F1 is descriptive, not a significance test.
