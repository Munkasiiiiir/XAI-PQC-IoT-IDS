# Resource-Aware Explainable ML for Post-Quantum-Secured IoT Intrusion Detection

Software-only research pipeline extending Sharma & Rani (2025) with:

- **IDS:** LightGBM (primary) + Random Forest (baseline)
- **XAI:** alert-level TreeSHAP
- **PQC:** ML-KEM / ML-DSA software microbenchmarks (host PC)

**Supervisor guidance:** hardware integration (Raspberry Pi / ESP32) skipped.

## Repository layout

```
datasets/ToN_IoT/     # ToN-IoT Network Train/Test CSV + audit
src/                  # preprocessing, IDS, XAI, PQC scripts
artifacts/            # processed splits + trained models
results/              # metrics, SHAP, PQC benchmarks
figures/              # manuscript figures
docs/                 # paper outline / supervisor memos
```

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas numpy scikit-learn lightgbm shap matplotlib seaborn joblib pyyaml pqcrypto cryptography python-docx

# Re-run pipeline (optional; results already included)
python src/02_preprocess.py
python src/03_train_ids.py
python src/04_xai_shap.py
python src/05_pqc_benchmark.py
```

## Dataset

Primary file: `datasets/ToN_IoT/train_test_network.csv`  
Source project: https://research.unsw.edu.au/projects/toniot-datasets  

Please cite the ToN_IoT authors (Alsaedi et al., 2020; Booij et al., 2022; Moustafa et al.) for academic use.

## Key results (included)

- Binary LightGBM F1 ≈ 0.998
- Multi-class LightGBM macro-F1 ≈ 0.954
- TreeSHAP ≈ 2.0 ms/alert (binary), ≈ 15.3 ms/alert (multi-class)
- ML-KEM-512 ops < 0.1 ms; ML-DSA-44 sign ≈ 6.9 ms (software-only)

See `results/joint_results_snapshot.txt` and `docs/Paper_Outline_Ahasan_Sir.docx`.

## Notes

- Large model artifacts are stored with **Git LFS**.
- This repository does **not** claim to be the first PQC+XAI+IDS system.
- PQC timings are host-PC software benchmarks only (not edge hardware).
