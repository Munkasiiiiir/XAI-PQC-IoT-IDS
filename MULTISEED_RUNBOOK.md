# Multi-seed experiment runbook (software-only)

## Run settings

| Item | Decision |
|---|---|
| Datasets | ToN-IoT Network (primary), UNSW-NB15, Edge-IIoTset |
| Seeds | `{42, 123, 2024}` per dataset (9 dataset-seed runs total) |
| Seed semantics | One master seed drives both the 80/20 stratified split and every model's `random_state` |
| Primary metric | multi-class macro-F1; binary F1 (positive class = attack) |
| Models | RF + LightGBM, binary + multi-class; hyperparameters frozen (no tuning) |
| Determinism | `PYTHONHASHSEED=0`, `THREADS=8`, LightGBM `deterministic=True`, `force_row_wise=True` |
| Dedupe | RAW rows before placeholder replacement and before column drops; then split |
| XAI | TreeSHAP `tree_path_dependent`, 200 predicted alerts, 10 warmup + 3 timed repeats |
| PQC | Not re-run; reuse `results/pqc_benchmarks.csv` with host-PC caveat |
| Statistics | mean ± sd and range only at n=3; no p-values; cross-dataset comparison is descriptive |
| Outputs | seed-scoped artifacts; append/upsert ledger `results/runs.csv`; never overwrite another seed |

## Commands

```bash
$env:PYTHONHASHSEED = "0"
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

## Expected raw files

| Dataset | Path | Source |
|---|---|---|
| ToN-IoT | `datasets/ToN_IoT/train_test_network.csv` | https://research.unsw.edu.au/projects/toniot-datasets |
| UNSW-NB15 | `datasets/UNSW_NB15/UNSW_NB15_training-set.csv` and `..._testing-set.csv` | https://research.unsw.edu.au/projects/unsw-nb15-dataset |
| Edge-IIoTset | `datasets/Edge_IIoTset/DNN-EdgeIIoT-dataset.csv` (or `ML-EdgeIIoT-dataset.csv`) | https://ieee-dataport.org/documents/edge-iiotset-... |

UNSW-NB15 is free for academic research (cite Moustafa & Slay 2015/2016).
Edge-IIoTset is CC BY 4.0 (cite Ferrag et al. 2022).

### Provenance of the copies actually used

The official UNSW SharePoint folder and the Kaggle/IEEE DataPort download both
require an interactive session, so the runs use public mirrors that were
validated against the official documentation:

- **UNSW-NB15** — `Mireu-Lab/UNSW-NB15` on Hugging Face. Its `test.csv`
  (175,341 rows) and `train.csv` (82,332 rows) were verified to have the
  documented 45 columns and were renamed to `UNSW_NB15_training-set.csv` and
  `UNSW_NB15_testing-set.csv` respectively (the mirror's own names are swapped
  relative to the official split). SHA-256 values are recorded in
  `datasets/registry.json`.
- **Edge-IIoTset** — `Sunayanajagadesh/ML_EdgeIIoT_dataset` on Hugging Face,
  `ML-EdgeIIoT-dataset.csv`. License CC BY 4.0; cite Ferrag et al. 2022.
  SHA-256 recorded in `datasets/registry.json`.

These are mirrors, not the official download endpoints; cite the original
authors, not the mirror, in the paper. The raw CSVs and trained model binaries
are intentionally not committed; the registry keeps their SHA-256 hashes and
the harness recreates the splits and models from the locked config.

## Ledger schema

`results/runs.csv` columns:
`run_id, dataset, seed, task, model, accuracy, precision, recall, f1, macro_f1,
weighted_f1, train_seconds, infer_ms_per_sample, model_size_mb, n_train, n_test,
config_hash, git_commit, timestamp`

`run_id = "<dataset>_s<seed>_<task>_<model>"`. Re-running a seed upserts its rows;
other runs are preserved.
