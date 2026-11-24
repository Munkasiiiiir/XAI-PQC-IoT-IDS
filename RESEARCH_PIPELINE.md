# Research Pipeline (Software-Only)

**Title:** Resource-Aware Explainable Machine Learning for Post-Quantum-Secured IoT Intrusion Detection  
**Supervisor decision:** Skip hardware integration (no Raspberry Pi / ESP32 deployment)  
**Primary dataset:** `datasets/ToN_IoT/train_test_network.csv`

---

## Architecture (three planes)

```
[ToN-IoT Network CSV]
        |
        v
 Preprocessing / Feature Selection
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
```

---

## Phase 0 — Setup (Day 1)

- [x] Novelty memo approved direction with Ahasan Sir
- [x] Skip hardware
- [x] Download ToN-IoT Network Train/Test
- [ ] Create Python environment
- [ ] Install: `pandas numpy scikit-learn lightgbm shap matplotlib seaborn joblib`

```bash
cd "/home/munkasiiiiir/Documents/Research with Ahasan Sir"
python3 -m venv .venv
source .venv/bin/activate
pip install pandas numpy scikit-learn lightgbm shap matplotlib seaborn joblib pyyaml
```

---

## Phase 1 — Dataset Audit (Day 1–2)  ← START HERE

**Goal:** Understand data before modeling.

- [ ] Load CSV; count rows/columns
- [ ] Class balance (`label`, `type`)
- [ ] Missing values and `-` placeholders
- [ ] Identify leakage features (`src_ip`, `dst_ip`, ports, etc.)
- [ ] Decide binary vs multi-class experiments

**Deliverable:** `datasets/ToN_IoT/dataset_audit_report.txt`

---

## Phase 2 — Preprocessing (Day 2–3)

**Goal:** Clean, encode, split safely.

1. Replace `-` with missing / category `unknown`
2. Drop leakage columns: `src_ip`, `dst_ip`, `src_port`, `dst_port`
3. Encode categoricals (ordinal/one-hot as appropriate)
4. Stratified train/test split (e.g., 80/20) — same split for all models
5. Optional: feature selection (mutual information / RF importance)
6. Save processed arrays: `artifacts/processed/`

**Deliverable:** preprocessing script + processed dataset files

---

## Phase 3 — Intrusion Detection Models (Day 3–5)

**Goal:** Establish detection baselines.

| Model | Role |
|---|---|
| Random Forest | Interpretable baseline |
| LightGBM | Primary detector |
| (Optional later) simple MLP/CNN | Compare vs Sharma & Rani spirit |

**Metrics (must report):**
- Accuracy, Precision, Recall, F1
- **Macro-F1** (imbalance)
- Per-class recall (especially `mitm`)
- Inference time, model size

**Tasks:** binary classification first, then multi-class.

**Deliverable:** `results/ids_metrics.csv` + confusion matrices

---

## Phase 4 — Explainability (Day 5–7)

**Goal:** Explain alerts; measure cost.

1. Fit TreeSHAP on LightGBM (and/or RF)
2. Global feature importance summary
3. Local explanations for sampled alerts only (not every row)
4. Measure:
   - explanation latency (ms/alert)
   - memory overhead
5. Optional offline LIME on a small sample for comparison

**Deliverable:** SHAP plots + `results/xai_overhead.csv`

---

## Phase 5 — PQC Software Benchmarks (Day 7–9)

**Goal:** Crypto overhead without hardware.

1. Install `liboqs` / `oqs-python` if available, or use documented library timings carefully
2. Benchmark on your PC:
   - ML-KEM (Kyber): KeyGen, Encaps, Decaps
   - ML-DSA (Dilithium): KeyGen, Sign, Verify
3. Record: mean latency, key/ciphertext/signature sizes
4. Compare vs classical baseline (e.g., ECDH/ECDSA) if available

**Deliverable:** `results/pqc_benchmarks.csv`  
**Do not claim:** Raspberry Pi / ESP32 validation

---

## Phase 6 — Joint Analysis (Day 9–11)

**Goal:** Answer the research questions.

Build one summary table:

| Component | Metric | Value |
|---|---|---|
| IDS | Macro-F1, latency | … |
| XAI | ms/explanation | … |
| PQC | ms/op, sizes | … |

Discuss bottlenecks: detection vs explanation vs crypto (software).

**Deliverable:** figures + discussion outline for paper

---

## Phase 7 — Writing (Day 11–end)

1. Related work (Sharma & Rani; Li et al.; XAI-IDS; PQC surveys)
2. Methodology (three planes; no hardware)
3. Results
4. Limitations (no physical edge deployment)
5. Conclusion

**Target narrative:**  
Resource-aware classical ML + measured TreeSHAP + software PQC as an alternative to Sharma & Rani’s deep IDS — distinct from Li et al.’s SDN/GNN setting.

---

## Folder structure to create

```
Research with Ahasan Sir/
├── datasets/ToN_IoT/
├── src/
│   ├── 01_audit_dataset.py
│   ├── 02_preprocess.py
│   ├── 03_train_ids.py
│   ├── 04_xai_shap.py
│   └── 05_pqc_benchmark.py
├── artifacts/
├── results/
├── figures/
└── docs/
```

---

## What NOT to do yet

- Do not implement ESP32 / Raspberry Pi code
- Do not claim first PQC+XAI+IDS paper
- Do not say XAI replaces deep learning
- Do not keep IP/port features in the main model
- Do not report accuracy alone under imbalance

---

## Immediate next action

**Finish Phase 1 audit → start Phase 2 preprocessing script.**
