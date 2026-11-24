# Multi-seed findings

n=3 seeds `{42, 123, 2024}`: mean ± sd. Cross-dataset macro-F1 is descriptive, not a head-to-head test.  
Ledger: `results/runs.csv`. Snapshot: `results/joint_results_snapshot.txt`.  
PQC (host PC, not re-run): ML-KEM-512 < 0.1 ms/op; ML-DSA-44 sign ≈ 6.9 ms.

## edge_iiot

Seeds: 42, 123, 2024 · 156,986 rows after dedupe · 42 features · 15 classes

| task/model | macro-F1 (mean±sd) | F1 | size MB | infer ms | SHAP ms/alert |
|---|---|---|---|---|---|
| binary/LightGBM | 0.9110±0.0016 | 0.9699±0.0006 | 2.0 | 0.0132 | 2.03±0.08 |
| binary/RandomForest | 0.9319±0.0016 | 0.9796±0.0004 | 98.1 | 0.0092 | n/a |
| multiclass/LightGBM | 0.8314±0.0022 | 0.8314±0.0022 | 35.8 | 0.2837 | 23.80±0.59 |
| multiclass/RandomForest | 0.8308±0.0017 | 0.8308±0.0017 | 1039.4 | 0.0232 | n/a |

## ton_iot

Seeds: 42, 123, 2024 · 190,474 rows after dedupe · 30 features · 10 classes

| task/model | macro-F1 (mean±sd) | F1 | size MB | infer ms | SHAP ms/alert |
|---|---|---|---|---|---|
| binary/LightGBM | 0.9968±0.0003 | 0.9986±0.0001 | 2.0 | 0.0245 | 3.35±0.44 |
| binary/RandomForest | 0.9968±0.0004 | 0.9986±0.0002 | 16.2 | 0.0094 | n/a |
| multiclass/LightGBM | 0.9546±0.0018 | 0.9546±0.0018 | 25.5 | 0.2868 | 28.69±3.29 |
| multiclass/RandomForest | 0.9530±0.0010 | 0.9530±0.0010 | 162.8 | 0.0228 | n/a |

## unsw_nb15

Seeds: 42, 123, 2024 · 257,673 rows after dedupe · 42 features · 10 classes

| task/model | macro-F1 (mean±sd) | F1 | size MB | infer ms | SHAP ms/alert |
|---|---|---|---|---|---|
| binary/LightGBM | 0.9443±0.0013 | 0.9580±0.0011 | 2.0 | 0.0125 | 4.16±0.15 |
| binary/RandomForest | 0.9467±0.0004 | 0.9614±0.0002 | 276.3 | 0.0154 | n/a |
| multiclass/LightGBM | 0.5912±0.0114 | 0.5912±0.0114 | 26.4 | 0.2253 | 41.66±0.59 |
| multiclass/RandomForest | 0.5833±0.0065 | 0.5833±0.0065 | 1110.0 | 0.0339 | n/a |

## Read-out notes

- **H1:** Multi-class LightGBM ≈ RF everywhere; binary RF ahead on Edge (and slightly on UNSW).
- **H2:** Holds — multi-class LightGBM ~25–36 MB vs RF ~163–1110 MB.
- **H3:** Multi-class SHAP ≫ binary, but not purely class-count driven (Edge 15 cls cheaper than UNSW 10).
- **H4:** Holds — ML-DSA-44 sign (~6.9 ms) dominates ML-KEM and IDS inference on this host.
- UNSW multi-class macro-F1 is rare-class sensitive; report per-class metrics in the paper.
