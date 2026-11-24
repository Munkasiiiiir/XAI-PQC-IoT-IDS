# Paper Outline / Draft Skeleton

**Working title:** Resource-Aware Explainable Machine Learning for Post-Quantum-Secured IoT Intrusion Detection

**Status:** Experimental Phases 1–5 completed (software-only). Hardware integration excluded per supervisor guidance.

**Base paper:** Sharma & Rani (2025), IEEE TCE. DOI: 10.1109/TCE.2025.3569904  
**Closest related work:** Li et al. (2026), Scientific Reports. DOI: 10.1038/s41598-026-76310-5

---

## Abstract (draft bullets)

- Quantum threats motivate PQC for IoT communication.
- Sharma & Rani combine PQC with deep IDS (CNN+VAE), but lack explainability and use a heavy detector.
- We propose a **three-plane software framework**: LightGBM/RF detection, alert-level TreeSHAP, and ML-KEM/ML-DSA software evaluation.
- On ToN-IoT Network (leakage-safe features): multi-class LightGBM macro-F1 ≈ 0.954; TreeSHAP ≈ 15.3 ms/alert; ML-KEM-512 ops < 0.1 ms; ML-DSA-44 sign ≈ 6.9 ms (host PC).
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
1. Leakage-aware classical ML IDS on ToN-IoT as alternative to Sharma & Rani’s CNN/VAE detector.
2. Alert-level TreeSHAP with measured explanation latency.
3. Software microbenchmarks of ML-KEM and ML-DSA vs classical ECDH/ECDSA.
4. Joint comparison of detection quality, explanation cost, and crypto cost.

### Explicit non-claims
- Not the first PQC+XAI+IDS paper (see Li et al., 2026).
- XAI does not replace detection models.
- No Raspberry Pi/ESP32 validation in this version.

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
- Dataset-driven IDS/XAI
- Host-PC PQC microbenchmarks

---

## 4. Methodology

### 4.1 Dataset
- ToN-IoT Network Train/Test CSV
- Cite Alsaedi et al. (2020), Booij et al. (2022)
- After dedup: 190,474 rows
- Drop leakage: `src_ip`, `dst_ip`, `src_port`, `dst_port`
- Drop sparse text fields: DNS query, HTTP URI, etc.
- 30 features retained
- Stratified 80/20 split on attack `type`

### 4.2 Models
- Binary + multi-class
- Class-weighted RF and LightGBM
- Metrics: Accuracy, Precision, Recall, F1, **macro-F1**, per-class report, inference time, model size

### 4.3 XAI
- TreeSHAP (`tree_path_dependent`)
- 200 alert samples
- Global mean(|SHAP|) + overhead (ms/alert)

### 4.4 PQC
- `pqcrypto`: ML-KEM-512/768/1024, ML-DSA-44/65/87
- `cryptography`: ECDH-P256, ECDSA-P256
- 100 iterations + warmup

---

## 5. Results

### 5.1 Detection
Insert Table: `results/ids_metrics.csv`  
Insert Fig: `figures/fig_ids_quality_vs_size.png`  
Insert Fig: `figures/fig_cm_multiclass_lightgbm.png`

**Key numbers (current experiments):**
- Binary LightGBM: Acc 0.9975, F1 0.9984, size 1.99 MB
- Multi-class LightGBM: Acc 0.9797, macro-F1 0.9539, size 25.5 MB
- Multi-class RF: macro-F1 0.9519 but size 163 MB

### 5.2 Explainability
Insert Fig: `figures/fig_shap_top_features_multiclass.png`  
Insert Fig: `figures/fig_detect_vs_explain_cost.png`  
Insert Table: `results/xai_overhead.csv`

- Binary TreeSHAP ≈ 2.03 ms/alert
- Multi-class TreeSHAP ≈ 15.29 ms/alert
- Top features: `src_ip_bytes`, `conn_state`, `duration`, …

### 5.3 PQC software overhead
Insert Fig: `figures/fig_pqc_latency.png`, `fig_pqc_sizes.png`  
Insert Table: `results/pqc_benchmarks.csv`

- ML-KEM-512: keygen/encaps/decaps ≈ 0.038 / 0.048 / 0.059 ms
- ML-DSA-44 sign ≈ 6.90 ms (dominant crypto cost)
- Classical ECDSA sign ≈ 0.024 ms

### 5.4 Joint trade-off
Insert Fig: `figures/fig_joint_cost_components.png`

**Finding:** For alert handling on this host, ML-DSA signing and multi-class TreeSHAP dominate over IDS inference and ML-KEM.

---

## 6. Discussion

- LightGBM offers strong accuracy with smaller footprint than RF for multi-class.
- Alert-only explanation policy keeps XAI practical.
- PQC is feasible in software; signature generation is the main latency driver.
- Distinct from Sharma & Rani (no XAI; DL detector) and Li et al. (SDN/GNN/control-plane focus).

### Limitations
- No physical IoT/edge hardware validation
- Single primary dataset (ToN-IoT Network)
- Host-PC timings are not transferable as absolute IoT device costs
- No adversarial robustness / concept drift study yet

---

## 7. Conclusion and Future Work

- Conclude three-plane software framework usefulness.
- Future: second dataset (UNSW-NB15 / Edge-IIoTset), optional hardware revisit if supervisor approves later, hybrid classical+PQC handshake study, explanation faithfulness tests.

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

- [x] Fig: IDS quality vs size
- [x] Fig: IDS inference latency
- [x] Fig: Multi-class confusion matrix
- [x] Fig: Detect vs explain cost
- [x] Fig: SHAP top features
- [x] Fig: PQC sizes
- [x] Fig: PQC latency
- [x] Fig: Joint cost components
- [x] Table: IDS metrics
- [x] Table: XAI overhead
- [x] Table: PQC benchmarks

---

## Immediate writing next steps

1. Expand Related Work into full paragraphs with citations.
2. Write Results section around the figures above.
3. Ask Ahasan Sir whether to add a second dataset before submission.
