# Paper Outline / Draft Skeleton

**Working title:** Resource-Aware Explainable Machine Learning for Post-Quantum-Secured IoT Intrusion Detection

**Status:** Multi-seed cross-dataset IDS/XAI benchmark completed (3 datasets × 3 seeds = 9 runs). PQC host-PC microbenchmarks completed earlier (not re-run). Hardware integration excluded per supervisor guidance.

**Base paper:** Sharma & Rani (2025), IEEE TCE. DOI: 10.1109/TCE.2025.3569904  
**Closest related work:** Li et al. (2026), Scientific Reports. DOI: 10.1038/s41598-026-76310-5

---

## Abstract (draft bullets)

- Quantum threats motivate PQC for IoT communication.
- Sharma & Rani combine PQC with deep IDS (CNN+VAE), but lack explainability and use a heavy detector.
- We propose a **three-plane software framework**: LightGBM/RF detection, alert-level TreeSHAP, and ML-KEM/ML-DSA software evaluation.
- Multi-seed evaluation (seeds `{42,123,2024}`) on **ToN-IoT, UNSW-NB15, and Edge-IIoTset**.
- Primary (ToN-IoT): multi-class LightGBM macro-F1 **0.9546±0.0018**; TreeSHAP **28.69±3.29** ms/alert (multi), **3.35±0.44** ms/alert (binary); ML-KEM-512 ops < 0.1 ms; ML-DSA-44 sign ≈ 6.9 ms (host PC).
- Cross-eval: Edge multi-class macro-F1 **0.8314±0.0022**; UNSW multi-class macro-F1 **0.5912±0.0114** (rare-class sensitive).
- Contribution is a joint trade-off analysis, **not** a claim of first PQC+XAI+IDS system.

---

## 1. Introduction

### Motivation
- IoT consumer/edge systems need long-term cryptographic security (harvest-now-decrypt-later).
- IDS decisions in security operations need interpretability.
- Resource constraints favor lightweight classical ML over deep models for many tabular IDS tasks.

### Problem statement
Can a lightweight classical ML IDS, with quantified TreeSHAP explanations and NIST PQC software overheads, serve as a practical alternative to deep PQC-integrated IDS frameworks—without SDN/GNN complexity and without hardware deployment in this study?

### Contributions (proposed, evidence-backed)
1. Leakage-aware classical ML IDS on ToN-IoT, with multi-seed cross-evaluation on UNSW-NB15 and Edge-IIoTset, as an alternative to Sharma & Rani’s CNN/VAE detector.
2. Alert-level TreeSHAP with measured explanation latency (mean ± sd over seeds).
3. Software microbenchmarks of ML-KEM and ML-DSA vs classical ECDH/ECDSA.
4. Joint comparison of detection quality, explanation cost, model size, and crypto cost.

### Explicit non-claims
- Not the first PQC+XAI+IDS paper (see Li et al., 2026).
- XAI does not replace detection models.
- No Raspberry Pi/ESP32 validation in this version.
- Cross-dataset scores are descriptive (n=3 seeds; no p-values).

---

## 2. Related Work

| Theme | Key refs | Gap relative to us |
|---|---|---|
| PQC + DL IDS | Sharma & Rani (2025) | No XAI; heavy DL |
| PQC + XAI + IDS (SDN/GNN) | Li et al. (2026) | Different setting; not resource-first classical edge software study |
| XAI IoT IDS | Abou El Houda et al.; Ebrahimi et al. | Usually no PQC joint cost |
| Constrained PQC | Fitzgibbon & Ottaviani (2024) | No IDS/XAI |
| AI+PQC SLR | Saeed & Alqahtani (2026) | Confirms integration still immature |

---

## 3. Threat Model and System Design

### Three planes
1. **Detection plane:** LightGBM (primary), Random Forest (baseline)
2. **Explanation plane:** TreeSHAP on predicted alerts only
3. **Crypto plane:** ML-KEM (key establishment), ML-DSA (signatures); classical baselines

### Scope
- Software evaluation only
- Dataset-driven IDS/XAI with locked hyperparameters
- Host-PC PQC microbenchmarks

---

## 4. Methodology

### 4.1 Datasets
| Dataset | Dedup rows | Features | Classes | Notes |
|---|---|---|---|---|
| ToN-IoT Network (primary) | 190,474 | 30 | 10 | Drop IP/port + sparse text; cite Alsaedi/Booij/Moustafa |
| UNSW-NB15 | 257,673 | 42 | 10 | Train+test union, then split; cite Moustafa & Slay |
| Edge-IIoTset (ML CSV) | 156,986 | 42 | 15 | Drop host/port/URI/payload fields; cite Ferrag et al. |

- Raw-row dedupe before placeholder cleaning (ToN restores the original 20,569 duplicate removals).
- Stratified 80/20 split on the multi-class label; master seed also sets model `random_state`.
- Provenance/hashes: `datasets/registry.json`.

### 4.2 Models
- Binary + multi-class; class-weighted RF and LightGBM
- Frozen hyperparameters (`writing/preanalysis.json`); no tuning
- Metrics: Accuracy, Precision, Recall, F1, **macro-F1**, per-class report, inference time, model size
- Report mean ± sd over seeds `{42, 123, 2024}`

### 4.3 XAI
- TreeSHAP (`tree_path_dependent`) on LightGBM only
- 200 alert samples; timed after warmup
- Global mean(|SHAP|) + overhead (ms/alert)

### 4.4 PQC
- `pqcrypto`: ML-KEM-512/768/1024, ML-DSA-44/65/87
- `cryptography`: ECDH-P256, ECDSA-P256
- 100 iterations + warmup; timings from earlier host-PC run (not re-executed in multi-seed batch)

---

## 5. Results

### 5.1 Detection
Insert Table: `results/ids_metrics.csv` / `results/MULTISEED_SUMMARY.md`  
Insert Fig: `figures/fig_ids_quality_vs_size.png` (refresh from multi-seed if needed)  
Insert Fig: `figures/fig_cm_multiclass_lightgbm.png`

**Key numbers (n=3 seeds, mean ± sd):**

| Dataset | Multi LGBM macro-F1 | Binary LGBM F1 | Multi LGBM size | Multi RF size |
|---|---|---|---|---|
| ToN-IoT | **0.9546±0.0018** | **0.9986±0.0001** | 25.5 MB | 162.8 MB |
| UNSW-NB15 | **0.5912±0.0114** | **0.9580±0.0011** | 26.4 MB | 1110.0 MB |
| Edge-IIoTset | **0.8314±0.0022** | **0.9699±0.0006** | 35.8 MB | 1039.4 MB |

- LightGBM matches RF on multi-class macro-F1 within ~0.01 on all three datasets.
- Binary: RF slightly ahead on Edge (macro-F1 0.9319 vs 0.9110) and marginally on UNSW.

### 5.2 Explainability
Insert Fig: `figures/fig_shap_top_features_multiclass.png`  
Insert Fig: `figures/fig_detect_vs_explain_cost.png`  
Insert Table: `results/xai_overhead.csv`

| Dataset | Binary SHAP ms/alert | Multi SHAP ms/alert |
|---|---|---|
| ToN-IoT | **3.35±0.44** | **28.69±3.29** |
| UNSW-NB15 | **4.16±0.15** | **41.66±0.59** |
| Edge-IIoTset | **2.03±0.08** | **23.80±0.59** |

- Top ToN features (seed 42 multi): `src_ip_bytes`, `conn_state`, `duration`, `src_bytes`, `dst_ip_bytes`, …

### 5.3 PQC software overhead
Insert Fig: `figures/fig_pqc_latency.png`, `fig_pqc_sizes.png`  
Insert Table: `results/pqc_benchmarks.csv`

- ML-KEM-512: keygen/encaps/decaps ≈ 0.038 / 0.048 / 0.059 ms
- ML-DSA-44 sign ≈ 6.90 ms (dominant crypto cost)
- Classical ECDSA sign ≈ 0.024 ms

### 5.4 Joint trade-off
Insert Fig: `figures/fig_joint_cost_components.png`

**Finding:** For alert handling on this host, **ML-DSA signing** and **multi-class TreeSHAP** dominate over IDS inference and ML-KEM. LightGBM preserves multi-class quality at a far smaller footprint than RF (~25–36 MB vs ~0.16–1.1 GB).

---

## 6. Discussion

- LightGBM offers strong multi-class accuracy with a much smaller footprint than RF.
- Alert-only explanation policy keeps XAI practical; cost is higher for multi-class than binary.
- SHAP cost does not scale by class count alone (Edge 15 classes cheaper than UNSW 10).
- UNSW multi-class macro-F1 is limited by rare classes (e.g. worms); report weighted/per-class metrics alongside macro-F1.
- PQC is feasible in software; signature generation is the main latency driver.
- Distinct from Sharma & Rani (no XAI; DL detector) and Li et al. (SDN/GNN/control-plane focus).

### Limitations
- No physical IoT/edge hardware validation
- Host-PC timings are not transferable as absolute IoT device costs
- ToN-IoT Network file is the common Train/Test subset (211k raw / 190k after dedupe), not the full 461k official release
- UNSW/Edge raw files used validated public mirrors (hashes in registry)
- No adversarial robustness / concept drift study yet
- n=3 seeds → report mean ± sd only; no significance tests

---

## 7. Conclusion and Future Work

- Conclude three-plane software framework usefulness under multi-seed, multi-dataset evaluation.
- Future: optional hardware revisit if supervisor approves, hybrid classical+PQC handshake study, explanation faithfulness tests, refresh manuscript figures from multi-seed outputs.

---

## Suggested paper structure length

| Section | Approx. pages |
|---|---|
| Intro | 1.0 |
| Related work | 1.5 |
| Design/method | 2.0 |
| Results | 2.5 |
| Discussion/limits | 1.0 |
| Conclusion | 0.5 |

**Target venues (software-focused):** IEEE Access, IoT journal special issues, JNCA, Computer Networks (confirm with Ahasan Sir).

---

## Figure/Table checklist for manuscript

- [x] Fig: IDS quality vs size *(refresh from multi-seed)*
- [x] Fig: IDS inference latency *(refresh from multi-seed)*
- [x] Fig: Multi-class confusion matrix
- [x] Fig: Detect vs explain cost *(refresh SHAP timings)*
- [x] Fig: SHAP top features
- [x] Fig: PQC sizes
- [x] Fig: PQC latency
- [x] Fig: Joint cost components
- [x] Table: IDS metrics (`results/ids_metrics.csv`)
- [x] Table: XAI overhead (`results/xai_overhead.csv`)
- [x] Table: PQC benchmarks
- [x] Table/appendix: multi-seed summary (`results/MULTISEED_SUMMARY.md`)

---

## Immediate writing next steps

1. Expand Related Work into full paragraphs with citations.
2. Write Results section around `results/MULTISEED_SUMMARY.md` and refreshed figures.
3. Explicitly discuss UNSW rare-class macro-F1 and binary H1 soft miss on Edge.
