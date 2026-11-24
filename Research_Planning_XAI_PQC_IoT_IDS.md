# Research Planning & Literature Review

## Topic
**A Resource-Aware Explainable Machine Learning Framework for Post-Quantum-Secured IoT Intrusion Detection**

**Base paper:** Sharma, A., & Rani, S. (2025). Post-Quantum Cryptography (PQC) for IoT-Consumer Electronics Devices Integrated With Deep Learning. *IEEE Transactions on Consumer Electronics*, 71(2), 4925–4933. https://doi.org/10.1109/TCE.2025.3569904

**Status of this document:** Academic feasibility study and literature synthesis. No experiments have been implemented. Claims of novelty are supported by comparison with verified prior work.

**Verification note:** Bibliographic details below were cross-checked via publisher pages / DOIs (IEEE Xplore, Springer Nature, MDPI, ACM, PeerJ, UNSW). Where a detail could not be fully confirmed from the publisher page, it is marked **[partially verified]**.

---

# Phase 1 — Understanding the Original Paper

## 1.1 What the original paper does

Sharma & Rani propose a **hybrid security framework** for IoT consumer electronics that combines:

1. **Post-quantum cryptography** for confidential and authenticated communication.
2. **Deep learning–based intrusion / anomaly detection** for identifying malicious behavior.

The two layers are complementary but **orthogonal**:

| Layer | Role | Does it detect attacks? | Does it encrypt traffic? |
|---|---|---|---|
| PQC (Kyber, code-based, SPHINCS+, hybrid classical+PQC) | Secure key exchange, encryption, signatures | No | Yes |
| DL-IDS (CNN + VAE + EWC) | Detect anomalous IoT / network behavior | Yes | No |

They evaluate on Raspberry Pi 4 and ESP32, and report PQC timings (e.g., key gen ≈ 12.5 ms, enc/dec ≈ 25.3 ms, latency ≈ 18.7 ms, throughput ≈ 5000 ops/s, energy ≈ 2.4 mJ) plus DL reconstruction / detection metrics (e.g., reconstruction accuracy ~97–99%, F1 ≈ 93.45%). Datasets used for IDS: **BoT-IoT** and **UNSW-NB15**. Case study: simulated smart grid with 500 meters.

## 1.2 Component roles (critical distinctions)

### Cryptographic components
- **Kyber:** lattice-based KEM for key exchange / encapsulation.
- **Code-based crypto:** message encryption for high-value traffic (large keys → selective use).
- **SPHINCS+:** hash-based signatures for authenticity / firmware-style integrity.
- **Hybrid crypto:** classical DH/RSA concatenated or dual-signed with PQC for migration.

### Detection components
- **CNN (graph-style message passing as described):** learns relational / local-global patterns; produces anomaly scores.
- **VAE:** reconstructs “normal” behavior; high reconstruction error → anomaly.
- **EWC (Elastic Weight Consolidation):** continual learning so the IDS adapts to new attacks without catastrophic forgetting.
- **Experience replay:** complements EWC.

### Important conceptual correction for your proposal
**XAI does not replace CNN/VAE.**  
XAI (SHAP, LIME, feature importance, rules) **explains** a detector’s decisions. The detector itself remains an ML/DL classifier or anomaly model. Your extension should therefore be framed as:

> Replace the **black-box DL detector** with a **lightweight classical ML detector**, and **add an XAI layer** on top, while **retaining / refining the PQC communication layer**.

## 1.3 Limitations and gaps in the original paper

Supported limitations / weaknesses visible in the paper itself or by methodological critique:

1. **No explainability:** decisions of CNN+VAE are opaque to analysts.
2. **Heavy IDS stack for constrained devices:** CNN+VAE+continual learning is costly relative to tree ensembles on edge gateways.
3. **Conceptual confusion risk:** the paper mixes graph CNN language with standard CNN wording; architecture clarity is uneven.
4. **Dataset choice:** BoT-IoT / UNSW-NB15 are common but not the most IoT-native modern options (ToN-IoT, Edge-IIoTset, CICIoT2023 are stronger IoT/IIoT alternatives).
5. **SPHINCS+ on tiny devices:** literature on constrained PQC generally prefers Kyber + Dilithium/Falcon over SPHINCS+ for latency and signature size.
6. **Integration evidence is thin:** PQC and DL are presented as one “framework,” but the paper does not deeply evaluate *joint* end-to-end pipeline cost (crypto + detection + response) under identical conditions.
7. **Limited discussion of feature leakage / evaluation rigor** typical of strong IDS papers (e.g., removing IPs/ports, stratified metrics, imbalance handling).
8. **No analyst-facing explanation quality metrics** (faithfulness, stability, explanation latency).

## 1.4 What to retain / modify / replace

| Component | Recommendation |
|---|---|
| Hybrid PQC communication (Kyber KEM + classical hybrid transition) | **Retain**, with NIST-aligned naming (ML-KEM / Kyber) |
| SPHINCS+ signatures | **Modify**: prefer Dilithium (ML-DSA) or Falcon for IoT; keep SPHINCS+ only as optional baseline |
| Code-based encryption for all traffic | **Modify**: selective use only, or drop if not needed for your threat model |
| CNN + VAE detector | **Replace** with classical ML (RF / LightGBM / XGBoost) |
| EWC continual learning | **Optional later**; not needed for v1 contribution |
| Raspberry Pi / ESP32 evaluation style | **Retain and strengthen** with joint resource profiling |
| BoT-IoT / UNSW-NB15 only | **Replace/augment** with ToN-IoT (+ one comparison set) |
| No XAI | **Add** TreeSHAP (+ optional LIME offline) |

---

# Phase 2 — Dataset Investigation: ToN_IoT

## 2.1 Source and credibility

- **Official page:** https://research.unsw.edu.au/projects/toniot-datasets  
- Collected at Cyber Range & IoT Labs, UNSW Canberra (ADFA).  
- Heterogeneous Industry 4.0 / IoT–IIoT testbed: telemetry, Windows/Linux OS logs, Zeek/Bro network traffic.  
- Free for academic use; authors require citation of the ToN_IoT papers.

### Core dataset papers (verified)

1. Alsaedi, A., Moustafa, N., Tari, Z., Mahmood, A., & Anwar, A. (2020). TON_IoT Telemetry Dataset… *IEEE Access*, 8, 165130–165150. https://doi.org/10.1109/ACCESS.2020.3022862  
2. Booij, T. M., Chiscop, I., Meeuwissen, E., Moustafa, N., & den Hartog, F. T. H. (2022). ToN_IoT: The Role of Heterogeneity… *IEEE Internet of Things Journal*, 9(1), 485–496. https://doi.org/10.1109/JIOT.2021.3085194  
3. Moustafa, N. (2021). A new distributed architecture… Network TON_IoT datasets. *Sustainable Cities and Society*. (cite as required by UNSW page)

**Verdict on credibility:** High. Widely used in peer-reviewed IoT IDS research; stronger IoT relevance than older generic IDS sets alone.

## 2.2 Structure and contents

ToN_IoT is a **family of datasets**, not one CSV:

| Subset | Content | Typical use |
|---|---|---|
| Telemetry / IoT sensors | Fridge, GPS, Modbus, weather, etc. | Device-level anomaly detection |
| Network (Zeek-derived) | Connection, DNS, SSL, HTTP, statistical, weird/violation features | Network IDS |
| Linux OS | Process / memory / disk / network traces | Host IDS |
| Windows OS | Performance-monitor style host features | Host IDS |

For an **IoT network intrusion detection** paper extending Sharma & Rani, the **processed Network Train/Test CSV** is the primary recommendation.

Reported network-feature organization (from secondary analyses consistent with UNSW descriptions):

- Connection: `ts`, IPs, ports, bytes, proto, service, duration, conn_state, …
- DNS / SSL / HTTP blocks
- Statistical packet/byte counts
- Weird/violation fields
- Labels: `label` (binary 0/1) and `type` (attack family)

Common attack types: **backdoor, DDoS, DoS, injection, MITM, password, ransomware, scanning, XSS**, plus **normal**.

## 2.3 Size, imbalance, quality

Secondary literature commonly reports ~**461,043** network records in frequently used processed subsets, with roughly:

- Normal ≈ 300,000  
- Many attack classes ≈ 20,000 each  
- **MITM ≈ 1,043** (severe minority)

Implications:

- Strong **class imbalance** → need stratified splits, macro-F1, per-class recall; consider class weights / SMOTE carefully (and report ablation).
- Missing / “-” values and categorical fields require explicit preprocessing.
- High risk of **identifier leakage** if `src_ip`, `dst_ip`, ports, timestamps are kept → remove or carefully justify.

## 2.4 Suitability for classical ML + XAI

| Criterion | Assessment |
|---|---|
| IoT intrusion detection | Suitable (designed for it) |
| Classical ML (RF/XGBoost/LightGBM) | Excellent fit (tabular features) |
| XAI (SHAP/LIME) | Excellent fit (feature attributions on tabular data) |
| Resource-aware edge experiments | Suitable for **offline training / gateway inference**; not for ESP32 training |
| Compatibility with original paper comparison | Good as modernization of BoT-IoT/UNSW-NB15 |
| Already used with XAI | Yes — e.g., Ebrahimi et al. (2025) use TON-IoT with SHAP/LIME |

## 2.5 Dataset recommendation

**Primary:** ToN_IoT **Network** Train/Test processed CSV.  
**Secondary (recommended):** one of:

- **UNSW-NB15** — fair comparison with Sharma & Rani, or  
- **Edge-IIoTset** — stronger IIoT edge narrative, or  
- **CICIoT2023** — if you later want cross-benchmark against HPQ-EAI-IDS.

**Not sufficient alone for hardware claims:** dataset experiments ≠ real PQC/XAI deployment cost. Keep dataset evaluation and hardware microbenchmarks **separate but jointly reported**.

---

# Phase 3 — Literature Review (≈18 verified papers)

## A. Base / closely related frameworks

### P1. Sharma & Rani (2025) — base paper
- **Title:** Post-Quantum Cryptography (PQC) for IoT-Consumer Electronics Devices Integrated With Deep Learning  
- **Venue:** IEEE Transactions on Consumer Electronics, 71(2)  
- **DOI:** https://doi.org/10.1109/TCE.2025.3569904  
- **Objective:** Hybrid PQC + DL-IDS for IoT consumer devices.  
- **Methods:** Kyber, code-based, SPHINCS+, hybrid classical+PQC; CNN+VAE+EWC.  
- **Datasets:** BoT-IoT, UNSW-NB15.  
- **Hardware:** Raspberry Pi 4, ESP32.  
- **Results:** Reported PQC timings and DL detection/reconstruction metrics.  
- **Gaps:** No XAI; heavy DL; limited joint resource analysis; SPHINCS+ may be suboptimal for tiny IoT.  
- **Relevance:** Direct baseline you extend.

### P2. Li et al. (2026) — closest prior art (PQC + XAI + IDS)
- **Title:** Hybrid post-quantum explainable AI intrusion detection with SDN for heterogeneous IoT networks  
- **Venue:** Scientific Reports  
- **DOI:** https://doi.org/10.1038/s41598-026-76310-5  
- **Objective:** HPQ-EAI-IDS combining graph IDS, explainability, and PQC-secured SDN control plane.  
- **Methods:** GNN + XGBoost; TreeSHAP; ML-KEM for controller communication; SDN mitigation as architectural extension.  
- **Dataset:** CICIoT2023.  
- **Hardware:** Primarily computational/crypto overhead analysis; SDN mitigation not physically validated.  
- **Results:** Emphasize detection performance + crypto overhead; network-level recovery metrics marked as anticipated.  
- **Gaps / caveats:** Complex GNN+SDN stack; PQC not protecting device data plane IDS features; limited constrained-device focus; affiliation/context unusual (Art & Design school) — treat scientifically as prior art but critically.  
- **Relevance:** **Most important novelty threat.** Shows PQC+XAI+IDS combination already published; your contribution must differ (resource-aware classical ML on edge, ToN-IoT, joint XAI+PQC cost, extension of Sharma & Rani without SDN/GNN).

### P3. Namratha & Singh (2026)
- **Title:** Quantum Resilient Explainable Autonomous IoT Security Framework Using Dual-Layer Blockchain for Edge Intelligence  
- **Venue:** International Journal of Communication Systems  
- **DOI:** https://doi.org/10.1002/dac.70588  
- **Objective:** Quantum-resilient explainable edge IoT security with blockchain.  
- **Methods:** Kyber512 + Dilithium2; dual-layer blockchain; complex DL detectors (transformer-TCN / graph attention).  
- **Results:** Claims very high accuracy (~99.4%) and latency/energy improvements.  
- **Gaps:** Heavy DL + blockchain; “explainable” claim may not equal rigorous XAI evaluation; hard to reproduce.  
- **Relevance:** Another PQC + “explainable” IoT security system; reinforces that superficial combination is no longer novel.

### P4. Saeed & Alqahtani (2026) — SLR
- **Title:** AI and post-quantum cryptography powered cybersecurity approaches for IoT systems: a literature review  
- **Venue:** PeerJ Computer Science  
- **DOI:** https://doi.org/10.7717/peerj-cs.3502  
- **Objective:** Systematic review of AI + PQC for IoT.  
- **Findings:** Integrated AI–PQC still early; trade-offs in compute/energy/latency poorly addressed; practical frameworks scarce.  
- **Relevance:** Independently confirms a **supported gap**: resource-efficient practical AI+PQC integration.

## B. XAI for IoT / IDS

### P5. Abou El Houda, Brik & Khoukhi (2022)
- **Title:** “Why Should I Trust Your IDS?”: An Explainable Deep Learning Framework for IDS in IoT Networks  
- **Venue:** IEEE Open Journal of the Communications Society  
- **DOI:** https://doi.org/10.1109/OJCOMS.2022.3188750  
- **Methods:** DNN IDS + RuleFit, LIME, SHAP (local + global).  
- **Datasets:** NSL-KDD, UNSW-NB15.  
- **Gaps:** No PQC; DL-centric; older datasets.  
- **Relevance:** Canonical XAI-IDS IoT framing.

### P6. Ebrahimi, Javidan, Akbari & Hosseini (2025)
- **Title:** Intrusion detection in the internet of things using convolutional neural networks: an explainable AI approach  
- **Venue:** Cybersecurity (Springer)  
- **DOI:** https://doi.org/10.1186/s42400-025-00369-2  
- **Methods:** Lightweight 1D-CNN; SHAP for feature selection + global/local explanation; LIME locally.  
- **Dataset:** TON-IoT.  
- **Results:** Acc/Prec/Rec/F1 ≈ 0.995 / 0.9949 / 0.9947 / 0.9947.  
- **Gaps:** No PQC; still DL; limited joint edge crypto profiling.  
- **Relevance:** Direct evidence that **ToN-IoT + SHAP/LIME** is established; your novelty cannot be “first XAI on ToN-IoT.”

### P7. IEEE Access (2024) — LIME/SHAP on MLP IDS
- **Title:** Explainable AI for Intrusion Detection Systems: LIME and SHAP Applicability on Multi-Layer Perceptron  
- **DOI:** https://doi.org/10.1109/ACCESS.2024.3368377  
- **Methods:** MLP IDS + LIME/SHAP; perturbation validation + survey.  
- **Relevance:** Methodological guidance for comparing SHAP vs LIME.

### P8. ICHOR A 2025 conference paper
- **Title:** Enhancing Industrial IoT Cybersecurity with Explainable AI: A SHAP and LIME-Based Intrusion Detection Methodology  
- **DOI:** https://doi.org/10.1109/ichora65333.2025.11017105  
- **Methods:** CVAE / DT / RF + SHAP/LIME; WUSTL-IIoT-2021.  
- **Relevance:** Classical ML + XAI for IIoT already exists.

### P9. ICADEIS 2025
- **Title:** Attack Detection on Edge IIoT Using Ensemble Learning and XAI Model Transparency  
- **DOI:** https://doi.org/10.1109/icadeis65852.2025.10933136  
- **Methods:** RF, XGBoost, LightGBM + SHAP; Edge-IIoTset.  
- **Results:** LightGBM ≈ 97.60% best among tested.  
- **Relevance:** Your exact classical ML + SHAP stack is already used in IIoT IDS (without PQC).

### P10. Al Rawajbeh et al. (2025)
- **Title:** Trustworthy Adaptive AI for Real-Time Intrusion Detection in Industrial IoT Security  
- **Venue:** IoT (MDPI)  
- **DOI:** https://doi.org/10.3390/iot6030053  
- **Methods:** Online/ensemble learning + SHAP; ToN_IoT & Bot-IoT; Raspberry Pi 5 testbed.  
- **Results:** ~96.4% accuracy, 2.1% FPR, ~35 ms detection latency.  
- **Relevance:** Edge + XAI + ToN_IoT already demonstrated; again without your PQC joint pipeline.

## C. Lightweight classical ML IDS

### P11. LIRAD (2024)
- **Title:** LIRAD: lightweight tree-based approaches on resource constrained IoT devices for attack detection  
- **Venue:** Cluster Computing (Springer)  
- **DOI:** https://doi.org/10.1007/s10586-024-04792-x  
- **Methods:** DT/RF/XGBoost; Boruta/WOA feature selection; SMOTE variants; pruning.  
- **Datasets:** CICIDS2017, EDGE-IIOT.  
- **Hardware:** Raspberry Pi.  
- **Results:** Up to ~99.99% / 99.5%; memory ~1.93–3.07 MB; execution ~4.09–4.26 s (reported setting).  
- **Relevance:** Strong evidence that **tree models on Pi are feasible**; supports your resource-aware claim.

## D. PQC for constrained IoT

### P12. Fernández-Caramés (2020)
- **Title:** From Pre-Quantum to Post-Quantum IoT Security…  
- **Venue:** IEEE Internet of Things Journal, 7(7), 6457–6480  
- **DOI:** https://doi.org/10.1109/JIOT.2019.2958788  
- **Type:** Foundational survey.  
- **Relevance:** Motivates PQC for IoT constraints.

### P13. Fitzgibbon & Ottaviani (2024)
- **Title:** Constrained Device Performance Benchmarking with the Implementation of Post-Quantum Cryptography  
- **Venue:** Cryptography (MDPI), 8(2), 21  
- **DOI:** https://doi.org/10.3390/cryptography8020021  
- **Hardware:** Raspberry Pi 4 (+ comparisons).  
- **Findings:** Kyber & Dilithium most efficient KEM/signature pair for constrained devices; Falcon best TLS handshake size; SPHINCS+ much slower / larger.  
- **Relevance:** Directly informs which PQC algorithms you should keep from Sharma & Rani.

### P14. Kyber on ESP32 (2025, arXiv)
- **Title:** Efficient Implementation of CRYSTALS-KYBER Key Encapsulation Mechanism on ESP32  
- **Link:** https://arxiv.org/html/2503.10207v1  
- **Findings:** Dual-core + crypto accelerators can reduce Kyber512-90s to ~8.8–11 ms ops.  
- **Status:** Preprint — cite carefully; useful for ESP32 feasibility.  
- **Relevance:** Supports ESP32 as crypto endpoint, not as XAI host.

## E. PQC + ML/IDS integration (without full XAI)

### P15. ICCUBEA 2023
- **Title:** Quantum-Resistant Wireless Intrusion Detection System using Machine Learning Techniques  
- **DOI:** https://doi.org/10.1109/iccubea58933.2023.10392127  
- **Methods:** DNN + Lattice-based Hash Trapdoor scheme.  
- **Relevance:** Early PQC+ML IDS hybrid; no XAI.

### P16. Scientific Reports (2025)
- **Title:** Quantum-aware secure blockchain intrusion detection system for industrial IoT networks  
- **DOI:** https://doi.org/10.1038/s41598-025-31985-0  
- **Methods:** CNN–LSTM IDS + lattice PQC signatures + QKD + blockchain; Edge-IIoTset / SWaT / XIIoTID.  
- **Relevance:** Heavy PQC+IDS integration; not lightweight XAI classical ML.

### P17. PeerJ CS (2024) smart-home hybrid
- **Title:** Hybrid computing framework security in dynamic offloading for IoT-enabled smart home system  
- **DOI:** https://doi.org/10.7717/peerj-cs.2211  
- **Methods:** ECC + PQC + blockchain + classical ML anomaly detectors + ANN offloading.  
- **Relevance:** Hybrid crypto + ML exists; not focused on XAI or Sharma-style consumer-electronics IDS.

## F. Foundational XAI methods

### P18. Lundberg & Lee (2017)
- **Title:** A Unified Approach to Interpreting Model Predictions (SHAP)  
- **Venue:** NeurIPS 2017  
- **arXiv DOI:** https://doi.org/10.48550/arXiv.1705.07874  
- **Relevance:** Foundational SHAP / TreeSHAP theory.

### P19. Ribeiro, Singh & Guestrin (2016)
- **Title:** “Why Should I Trust You?”: Explaining the Predictions of Any Classifier (LIME)  
- **Venue:** KDD 2016  
- **DOI:** https://doi.org/10.1145/2939672.2939778  
- **Relevance:** Foundational LIME; use mainly for offline local comparison.

### P20. Alsaedi et al. (2020) / Booij et al. (2022)
- Already covered in Phase 2 as dataset foundations.

---

# Phase 4 — Comparative Literature Matrix

| No. | Paper | Year | IDS Algorithm | XAI | PQC | Dataset | Hardware | Key Findings | Limitations |
|---:|---|---:|---|---|---|---|---|---|---|
| 1 | Sharma & Rani | 2025 | CNN+VAE+EWC | None | Kyber, code-based, SPHINCS+, hybrid | BoT-IoT, UNSW-NB15 | RPi4, ESP32 | Joint PQC+DL framing; reported crypto timings | No XAI; heavy DL; weak joint cost analysis |
| 2 | Li et al. HPQ-EAI-IDS | 2026 | GNN+XGBoost | TreeSHAP | ML-KEM | CICIoT2023 | Overhead analysis | Closest PQC+XAI+IDS combo | SDN/GNN-heavy; limited edge validation |
| 3 | Namratha & Singh QRE-DLB | 2026 | Transformer-TCN / GAT-like | “Explainable” claim | Kyber, Dilithium | [not fully extracted here] | Edge-oriented claims | PQC+blockchain+detection | Complex; reproducibility concerns |
| 4 | Saeed & Alqahtani SLR | 2026 | Review (LSTM/RL focus) | Review | Review (Kyber/LWE/NTRU) | Literature | N/A | AI–PQC integration still immature | Not an empirical system |
| 5 | Abou El Houda et al. | 2022 | DNN | RuleFit, LIME, SHAP | None | NSL-KDD, UNSW-NB15 | Server-style | Strong XAI-IDS IoT template | No PQC; older data |
| 6 | Ebrahimi et al. | 2025 | 1D-CNN | SHAP, LIME | None | TON-IoT | Constrained-oriented DL | High accuracy + explanations on ToN-IoT | No PQC |
| 7 | IEEE Access LIME/SHAP MLP | 2024 | MLP | LIME, SHAP | None | IoT IDS setting | Not edge-focused | SHAP/LIME comparison methodology | No PQC |
| 8 | ICHOR A IIoT XAI | 2025 | CVAE, DT, RF | SHAP, LIME | None | WUSTL-IIoT-2021 | Not Pi-focused | Classical ML + XAI works | No PQC |
| 9 | ICADEIS Edge-IIoT XAI | 2025 | RF, XGB, LightGBM | SHAP | None | Edge-IIoTset | Not emphasized | LightGBM+SHAP strong | No PQC |
| 10 | Al Rawajbeh et al. | 2025 | Adaptive/online ensemble | SHAP | None | ToN_IoT, Bot-IoT | Raspberry Pi 5 | Real-time edge XAI IDS | No PQC |
| 11 | LIRAD | 2024 | DT, RF, XGBoost | None (inherent tree interpretability) | None | CICIDS2017, EDGE-IIOT | Raspberry Pi | Tree models fit constrained devices | No PQC/XAI layer |
| 12 | Fernández-Caramés | 2020 | Survey | None | Survey | N/A | N/A | PQC IoT roadmap | Pre-NIST-final era partly |
| 13 | Fitzgibbon & Ottaviani | 2024 | None | None | Kyber, Dilithium, Falcon, SPHINCS+, etc. | N/A | Raspberry Pi 4 | Kyber+Dilithium preferred | No IDS |
| 14 | Kyber ESP32 preprint | 2025 | None | None | Kyber | N/A | ESP32 | Kyber feasible on ESP32 | Preprint; no IDS |
| 15 | ICCUBEA WIDS+PQC | 2023 | DNN | None | Lattice hash trapdoor | Wireless IDS setting | Not fully edge-profiled | Early PQC+IDS | No XAI |
| 16 | QASB-IDS | 2025 | CNN-LSTM | None | Lattice signatures (+QKD) | Edge-IIoTset, SWaT, XIIoTID | IIoT-oriented | Blockchain+PQC+IDS | Heavy architecture |
| 17 | PeerJ smart-home hybrid | 2024 | Classical ML + ANN | None | ECC+PQC hybrid | Smart-home setting | Edge/fog/cloud | Hybrid crypto+ML offloading | No XAI focus |
| 18 | Lundberg & Lee SHAP | 2017 | N/A | SHAP | None | N/A | N/A | Theory of SHAP | Foundational |
| 19 | Ribeiro et al. LIME | 2016 | N/A | LIME | None | N/A | N/A | Theory of LIME | Foundational |

### Matrix synthesis

**Already established**
- XAI for IoT IDS (SHAP/LIME)
- Classical tree ensembles for IoT/IIoT IDS
- PQC on Raspberry Pi / ESP32
- PQC + IDS hybrids
- At least one published **PQC + XAI + IDS** system (HPQ-EAI-IDS)
- ToN-IoT + SHAP already used

**Insufficiently investigated (supported)**
- **Resource-aware classical ML IDS + TreeSHAP + NIST PQC**, jointly measured on constrained hardware, as a **lightweight alternative** to Sharma & Rani’s CNN+VAE stack
- Explicit **trade-off analysis** among detection quality, explanation latency/cost, and PQC handshake/crypto cost on the **same edge pipeline**
- Careful separation of: (a) dataset IDS performance, (b) XAI overhead, (c) PQC microbenchmarks, (d) end-to-end gateway latency

---

# Phase 5 — Research Gap and Novelty Assessment

## 5.1 Has your idea already been implemented?

**Not in the exact form you propose**, but **major pieces already exist**.

- Exact Sharma & Rani extension with classical ML + XAI: **not found** in the reviewed literature.
- Exact triple combination PQC + XAI + IoT IDS: **yes, already published** (Li et al., 2026; related claims in Namratha & Singh, 2026).
- Classical ML + SHAP IoT IDS: **yes, many times**.
- ToN-IoT + XAI: **yes**.

Therefore: **novelty is conditional**, not automatic.

## 5.2 Papers combining PQC, XAI, and IoT IDS

| Paper | Combination | Difference from your idea |
|---|---|---|
| Li et al., 2026 | GNN+XGBoost + TreeSHAP + ML-KEM + SDN | Graph/SDN-centric; CICIoT2023; not resource-first classical edge IDS |
| Namratha & Singh, 2026 | PQC + blockchain + “explainable” DL | Heavy DL/blockchain; not lightweight classical ML focus |

## 5.3 What would distinguish your work?

A publishable distinction must be **more than algorithm swapping**. Strongest differentiation:

1. **Explicit extension / critique of Sharma & Rani (2025):** replace opaque DL IDS with lightweight ML while preserving PQC channel security.  
2. **Resource-aware joint evaluation:** accuracy + macro-F1 + inference latency + RAM + energy + **explanation latency** + **PQC KEM/signature cost** on Raspberry Pi (and crypto-only on ESP32).  
3. **Architectural clarity:** three separated planes — Communication (PQC), Detection (ML), Explanation (XAI).  
4. **Dataset modernization:** ToN-IoT Network (+ one baseline dataset).  
5. **Practical PQC algorithm choice justified by constrained-device literature:** Kyber + Dilithium (not SPHINCS+ as default).  
6. **Explainability as operational cost**, not only plots: measure when explanations are generated (always vs on-alert only).

## 5.4 Is replacing DL with classical ML + XAI a meaningful contribution?

**Yes, if and only if** you demonstrate measurable advantages on constrained devices, for example:

- comparable detection quality at lower RAM/CPU/energy than CNN+VAE  
- lower detection latency  
- usable explanations at acceptable extra cost  
- PQC still within real-time / near-real-time budgets  

**No**, if you only report “RF got 99% and SHAP plots look nice.” That is incremental and crowded.

## 5.5 Can lightweight ML + explainability help on constrained devices?

**Supported by literature:** yes for tree models on Raspberry Pi (LIRAD; Al Rawajbeh et al.).  
**Caveats:**

- Full SHAP on every packet is expensive → use **TreeSHAP**, and explain **alerts only**.  
- ESP32 is suitable for **PQC crypto endpoints**, not for hosting XGBoost+SHAP.  
- Put IDS+XAI on **gateway / Raspberry Pi**; put Kyber on device or gateway depending on threat model.

## 5.6 Gaps supported by literature (not assumptions)

**Confirmed gaps**
1. Practical, resource-efficient **AI + PQC** integration remains underdeveloped (Saeed & Alqahtani, 2026).  
2. Sharma & Rani provide PQC+DL without explainability.  
3. Existing PQC+XAI+IDS work is not focused on **lightweight classical ML edge trade-offs** against a CNN+VAE baseline.  
4. Few studies jointly report **XAI overhead + PQC overhead + IDS metrics** on the same constrained platform.

**Not a gap**
- “Nobody used SHAP for IoT IDS.”  
- “Nobody used ToN-IoT.”  
- “Nobody combined PQC and IDS.”  
- “XAI replaces deep learning.”

## 5.7 What contribution could fit a reputable journal?

Target venues (realistic): *IEEE Internet of Things Journal*, *IEEE Transactions on Consumer Electronics*, *IEEE Access*, *Ad Hoc Networks*, *Computer Networks*, *Journal of Network and Computer Applications*, *IoT* (MDPI) — depending on depth of hardware validation.

A suitable contribution statement:

> We present a resource-aware, three-plane IoT security framework that (i) secures device–gateway communication with NIST PQC (ML-KEM/Kyber and ML-DSA/Dilithium), (ii) detects intrusions using lightweight tree-based ML on ToN-IoT, and (iii) provides on-alert TreeSHAP explanations, with a unified evaluation of detection quality, explanation cost, and cryptographic overhead on Raspberry Pi / ESP32 relative to a deep-learning IDS baseline inspired by Sharma & Rani.

---

# Phase 6 — Recommended Methodology

## 6.1 Conceptual architecture (three planes)

```
IoT Device (ESP32)                  Edge Gateway (Raspberry Pi 4/5)
-----------------                   --------------------------------
Sense / send data  --PQC channel-->  Decrypt / verify (Kyber/Dilithium)
                                     Feature extraction (flow/telemetry)
                                     Classical ML detector (LightGBM/RF)
                                     If alert: TreeSHAP explanation
                                     Log + analyst response
```

Do **not** claim XAI runs on ESP32 unless measured.

## 6.2 Recommended algorithm combination (keep it small)

### Primary recommendation
- **Detector:** LightGBM *(or Random Forest as simpler alternative)*  
- **XAI:** TreeSHAP (global summary + local on-alert explanations)  
- **Secondary XAI (optional offline):** LIME for comparison on a sample of alerts  
- **PQC:**  
  - KEM: **Kyber / ML-KEM**  
  - Signature: **Dilithium / ML-DSA**  
  - Baseline classical: ECDH/ECDSA or RSA for overhead comparison  
  - Optional: hybrid classical+PQC handshake

### Why this combination
- Tree models are strong on tabular IDS features and edge-friendly.  
- TreeSHAP is efficient and consistent relative to LIME for forests/boosting.  
- Kyber+Dilithium is repeatedly shown more practical than SPHINCS+ on constrained devices.  
- Avoid SVM as primary (scaling/kernel cost) unless as a small baseline.

## 6.3 Data / ML pipeline

1. Use ToN_IoT Network Train/Test splits.  
2. Drop leakage-prone identifiers (`src_ip`, `dst_ip`, raw ports if unjustified, maybe `ts`).  
3. Encode categoricals; impute “-”/missing.  
4. Feature selection: mutual information / RF importance / TreeSHAP-guided pruning.  
5. Handle imbalance: class weights first; SMOTE only with ablation.  
6. Metrics: Accuracy, Precision, Recall, F1, **macro-F1**, per-class recall, ROC-AUC, detection latency, model size, RAM, CPU.  
7. XAI metrics: explanation latency, memory, stability (jitter across runs), qualitative analyst usefulness; optional faithfulness via feature perturbation.  
8. Compare against:  
   - Sharma-style DL baseline (CNN or CNN+autoencoder simplified reimplementation)  
   - RF / XGBoost / LightGBM  
   - With vs without explanation-on-alert

## 6.4 PQC experiments

On Raspberry Pi and ESP32 (liboqs / wolfSSL / PQClean as available):

- KeyGen / Encaps / Decaps latency  
- Sign / Verify latency  
- CPU, RAM, energy if measurable  
- Handshake size vs classical  
- Hybrid vs pure PQC  

Keep PQC experiments **independent** of IDS accuracy claims, then report an **end-to-end gateway timeline**: decrypt → infer → (optional) explain.

## 6.5 What can be evaluated where

| Evaluation | Dataset/simulation | Raspberry Pi | ESP32 |
|---|---|---|---|
| IDS accuracy / F1 | Yes | Inference timing yes | Generally no |
| TreeSHAP cost | Yes | Yes | No |
| PQC microbenchmarks | Simulation optional | Yes | Yes |
| End-to-end secure pipeline | Partial | Yes | Device-side crypto only |
| Smart-grid case study | Simulation | Optional prototype | Sensors only |

---

# Phase 7 — Research Questions & Contributions

## Research Questions

1. **RQ1:** Can a lightweight tree-based IDS achieve detection performance comparable to a CNN/autoencoder-style deep IDS on ToN-IoT under resource constraints?  
2. **RQ2:** What is the added computational cost of on-alert TreeSHAP explanations on a Raspberry Pi gateway, and does it remain acceptable for near-real-time IoT security operations?  
3. **RQ3:** How do NIST PQC primitives (Kyber/Dilithium), alone and in hybrid classical+PQC mode, affect latency, memory, and energy on Raspberry Pi and ESP32 relative to classical public-key baselines?  
4. **RQ4:** In a combined PQC-secured communication + explainable ML detection pipeline, what are the dominant bottlenecks (crypto vs inference vs explanation), and which design choices minimize total edge overhead without collapsing detection quality?  
5. **RQ5 (optional):** Do SHAP attributions remain stable and actionable across attack classes under severe imbalance (e.g., MITM)?

## Measurable contributions (each tied to an experiment)

1. **C1 — Lightweight explainable detector for PQC-oriented IoT security:** Replace Sharma & Rani’s DL IDS with LightGBM/RF + TreeSHAP; experiment = ToN-IoT detection + explanation quality/cost.  
2. **C2 — Joint resource profile of detection and explanation:** Experiment = Pi measurements of inference vs on-alert explanation latency/RAM.  
3. **C3 — Constrained-device PQC characterization for the framework:** Experiment = Kyber/Dilithium vs classical (and optional SPHINCS+) on Pi/ESP32.  
4. **C4 — End-to-end three-plane framework evaluation:** Experiment = decrypt→detect→explain timeline and bottleneck analysis.  
5. **C5 — Evidence-based algorithm recommendation for consumer IoT gateways:** Experiment = ablation over model family, feature subset size, explanation policy (always vs on-alert).

---

# Phase 8 — Final Recommendation

## A. Should you proceed?

### **Yes, but with modifications.**

Reasons:
- The broad idea is timely and journal-relevant.  
- But **PQC + XAI + IoT IDS is no longer untouched novelty**.  
- Proceed only if you reposition around **resource-aware classical ML**, **joint cost evaluation**, and a **clean three-plane architecture** extending Sharma & Rani.  
- Do **not** proceed with a claim that “XAI replaces deep learning.”

## B. Title options

1. **Recommended:** *Resource-Aware Explainable Machine Learning for Post-Quantum-Secured IoT Intrusion Detection on Constrained Edge Devices*  
2. *A Three-Plane Framework for PQC-Enabled IoT Security: Lightweight Detection, TreeSHAP Explanations, and Kyber/Dilithium Overheads*  
3. *From Deep Learning to Explainable Edge Intelligence: Re-engineering PQC-Integrated IoT Intrusion Detection for Resource-Constrained Devices*

**Strongest:** Title 1 — clear, honest, searchable, not overclaiming.

## C. Dataset

- **Primary:** ToN_IoT Network Train/Test  
- **Secondary:** UNSW-NB15 (continuity with Sharma & Rani) **or** Edge-IIoTset (edge narrative)  
- Cite Alsaedi et al. (2020) and Booij et al. (2022) as required.

## D. ML + XAI + PQC selection

| Role | Choice |
|---|---|
| Main detector | LightGBM (RF as transparent baseline) |
| Optional detector baselines | Decision Tree, XGBoost |
| XAI | TreeSHAP primary; LIME optional offline |
| PQC KEM | Kyber / ML-KEM |
| PQC signature | Dilithium / ML-DSA |
| Avoid as default | SPHINCS+ on ESP32; SVM as main model; explaining every packet |

## E. What to do first (roadmap)

1. **Deep-read & annotate** Sharma & Rani + Li et al. (HPQ-EAI-IDS) + Saeed & Alqahtani SLR.  
2. **Finalize novelty statement** relative to those three.  
3. **Download ToN_IoT**, inspect class counts, missingness, leakage features.  
4. **Write related-work matrix** (this document is your start).  
5. **Define threat model** (quantum adversary for crypto; classical network attacker for IDS).  
6. **Freeze metrics and hardware plan** before coding.  
7. Implement **ML IDS only** on ToN-IoT.  
8. Add **TreeSHAP** and measure overhead.  
9. Benchmark **PQC** on Pi/ESP32.  
10. Integrate **end-to-end gateway pipeline**.  
11. Compare against a **DL baseline**.  
12. Draft paper only after tables/figures are stable.

## F. What to avoid

1. Claiming XAI *replaces* DL.  
2. Claiming first PQC+XAI+IDS paper.  
3. Using too many algorithms (RF+XGB+LGBM+SVM+DT+CNN+VAE…).  
4. Running SHAP on ESP32.  
5. Keeping IP/port features and calling results “real-world ready.”  
6. Reporting only accuracy under imbalance.  
7. Mixing QKD / blockchain / SDN unless essential — they dilute focus.  
8. Reproducing Sharma & Rani’s SPHINCS+-heavy stack without justification.  
9. Fabricating hardware energy numbers.  
10. Treating dataset accuracy as proof of deployable IoT security.

---

# Bottom Line

Your direction **can become a scientifically meaningful and publishable extension**, but only if repositioned as:

> **A resource-aware, explainable classical-ML alternative to the deep IDS in Sharma & Rani, co-designed with practical NIST PQC on constrained IoT/edge hardware, with joint measurement of detection, explanation, and cryptographic costs.**

If you keep the current framing as “XAI replaces CNN/VAE and this combination is novel,” the paper will be weak against existing literature.

**Next immediate action (before any implementation):** critically compare your planned architecture paragraph-by-paragraph with Li et al. (2026) and write a 1-page novelty memo for Ahasan Sir answering: *What do we do that HPQ-EAI-IDS and Sharma & Rani do not?*
