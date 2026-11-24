# Research Novelty and Proposed Contributions Memo

**Prepared for:** Ahasan Sir  
**Prepared by:** [Student Name]  
**Date:** 13 November 2026  
**Status:** Pre-implementation proposal (no experimental results claimed)

---

## 1. Research Title

**Resource-Aware Explainable Machine Learning for Post-Quantum-Secured IoT Intrusion Detection on Constrained Edge Devices**

---

## 2. Research Background and Motivation

Sharma & Rani (2025) integrate post-quantum cryptography (PQC) with deep learning–based intrusion detection for IoT consumer electronics (DOI: [10.1109/TCE.2025.3569904](https://doi.org/10.1109/TCE.2025.3569904)). Their work motivates quantum-resilient IoT security, but the detector (CNN + VAE, with continual learning) remains opaque and computationally demanding for constrained edge settings.

This proposal does **not** treat explainable AI (XAI) as a replacement for deep learning. Detection, explanation, and cryptography are separated into three planes:

| Plane | Role | Proposed technique |
|---|---|---|
| Intrusion detection | Classify normal vs attack traffic | LightGBM (primary); Random Forest (baseline) |
| Explainability | Interpret alerts for analysts | TreeSHAP (alert-level); LIME only if measurably useful offline |
| Post-quantum security | Secure communication / authentication | ML-KEM (Kyber); ML-DSA (Dilithium) |

---

## 3. Comparison With Existing Research

### Sharma & Rani (2025)
**Already contributes:** Hybrid PQC (Kyber, code-based crypto, SPHINCS+, classical–PQC hybrid) + DL-IDS (CNN + VAE + EWC); evaluation on Raspberry Pi 4 and ESP32; BoT-IoT / UNSW-NB15; reported crypto timings and detection/reconstruction metrics.  
**Not addressed:** Explainability; quantified explanation overhead; resource-first classical ML as an alternative detector; joint end-to-end cost of *detect → explain* under PQC-secured communication.

### Li et al. (2026)
**Already contributes:** HPQ-EAI-IDS combining GNN + XGBoost, TreeSHAP, and ML-KEM for SDN control-plane protection; CICIoT2023-focused detection evaluation; crypto/computational overhead analysis (DOI: [10.1038/s41598-026-76310-5](https://doi.org/10.1038/s41598-026-76310-5)). The authors explicitly state that SDN mitigation is an architectural extension and that network-recovery metrics are anticipated rather than physically validated.  
**Not addressed (from available evidence):** A lightweight classical-ML alternative to Sharma & Rani’s CNN/VAE stack; ToN-IoT-centred evaluation; Raspberry Pi / ESP32 constrained-device pipeline for IDS + XAI + PQC together; alert-policy measurement of explanation cost on edge hardware. ML-KEM secures controller communication and is **not** part of the detection model.

**Important:** This proposal does **not** claim to be the first PQC + XAI + IoT IDS framework. Li et al. already combine those themes in an SDN/GNN setting.

| Research Dimension | Sharma & Rani (2025) | Li et al. (2026) | Proposed Research |
|---|---|---|---|
| Detection architecture | CNN + VAE (+ EWC) | GNN + XGBoost | LightGBM (+ RF baseline) |
| Explainability | Not reported | TreeSHAP | TreeSHAP (alert-level); LIME optional offline |
| PQC implementation | Kyber, code-based, SPHINCS+, hybrid | ML-KEM (control plane) | ML-KEM + ML-DSA in device–gateway pipeline |
| Resource efficiency | Claimed for PQC; DL cost less central | Not established as resource-first edge focus | Primary design objective |
| Hardware evaluation | Raspberry Pi 4, ESP32 | Overhead analysis; physical SDN testbed not established | Pi for IDS/XAI; Pi + ESP32 for PQC |
| Explanation overhead | Not reported | Not established as edge latency/RAM study | Explicitly measured |
| End-to-end evaluation | Framework-level; joint detect–explain–crypto cost limited | Detection + crypto overhead; SDN response analytical | Decrypt → detect → explain timeline on edge |

---

## 4. Identified Research Gap

**Working claim (to be treated as a hypothesis, not settled fact):**  
While PQC-integrated IoT IDS and XAI-based IoT IDS have each been studied—and Li et al. already combine PQC, XAI, and IDS in an SDN/GNN context—a **resource-first classical ML approach that jointly evaluates detection quality, explanation overhead, and PQC overhead inside a constrained edge pipeline**, as a direct alternative to Sharma & Rani’s deep detector, appears **insufficiently investigated** based on the methodologies and experimental scopes of the two closest papers and related literature reviewed to date.

This claim remains open until a broader related-work sweep is finalised; it is **not** equivalent to “no prior PQC+XAI+IDS work exists.”

---

## 5. Proposed Research Methodology

1. **Datasets:** ToN-IoT Network Train/Test (primary); UNSW-NB15 or Edge-IIoTset (cross-evaluation).  
2. **Preprocessing:** Cleaning, encoding, imbalance-aware metrics, feature selection, removal of identifier leakage (e.g., raw IPs/ports where unjustified).  
3. **IDS:** LightGBM primary; Random Forest baseline; optional simplified DL baseline for fair comparison with Sharma & Rani.  
4. **XAI:** TreeSHAP on **alerts only**; LIME only if it adds measurable offline value.  
5. **PQC:** ML-KEM / ML-DSA microbenchmarks and hybrid classical comparison.  
6. **Hardware mapping:**  
   - **Raspberry Pi:** IDS inference, TreeSHAP, gateway-side PQC, end-to-end timeline.  
   - **ESP32:** PQC key exchange / auth endpoints only — **not** SHAP hosting unless later proven feasible.

---

## 6. Expected Novel Contributions

*(Proposed; contingent on experimental validation)*

1. A **resource-aware classical ML detector** positioned as a practical alternative to Sharma & Rani’s CNN/VAE IDS under edge constraints.  
2. **Quantified alert-level TreeSHAP overhead** (latency, CPU, RAM) on Raspberry Pi, separate from detection cost.  
3. **Constrained-device evaluation of ML-KEM and ML-DSA** within the same security pipeline (Pi + ESP32), with classical crypto baselines.  
4. A **joint decrypt → detect → explain** measurement that identifies the dominant bottleneck on constrained edge hardware.  
5. Evidence-based design guidance on whether explanation-on-alert remains operationally affordable under PQC-secured IoT communication.

---

## 7. Research Significance

If validated, the work would give IoT/edge practitioners a clearer answer than currently available from Sharma & Rani or Li et al.: whether a lightweight, explainable classical detector can preserve useful detection quality while keeping PQC and explanation costs within constrained-device budgets—without requiring an SDN/GNN control-plane architecture.

**Central answer for supervision:**  
Our contribution is **not** inventing PQC+XAI+IDS. It is a **resource-first, three-plane edge evaluation**—lightweight detection, measured explanation cost, and NIST PQC overhead—offered as a constrained-device alternative to Sharma & Rani’s deep IDS and as a distinct setting from Li et al.’s SDN/GNN framework.

---

**Requested decision:** Approval to proceed with dataset audit and experimental design freeze before implementation.
