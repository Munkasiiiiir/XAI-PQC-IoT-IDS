# Multi-seed findings

n=8 seeds `{7, 13, 19, 42, 123, 2024, 2025, 2026}`: mean ± sd.  
Cross-dataset macro-F1 is descriptive, not a head-to-head test.  
Ledger: `results/runs.csv`. Extension record: `writing/preanalysis_extension.json`.  
PQC (host PC, not re-run): ML-KEM-512 < 0.1 ms/op; ML-DSA-44 sign ≈ 6.9 ms.

## edge_iiot

Seeds: 7, 13, 19, 42, 123, 2024, 2025, 2026 · 156,986 rows after dedupe · 42 features · 15 classes

| task/model | macro-F1 (mean±sd) | F1 | size MB | infer ms | SHAP ms/alert |
|---|---|---|---|---|---|
| binary/LightGBM | 0.9102±0.0018 | 0.9695±0.0008 | 2.0 | 0.0131 | 2.59±0.69 |
| binary/RandomForest | 0.9336±0.0017 | 0.9801±0.0005 | 98.6 | 0.0123 | n/a |
| multiclass/LightGBM | 0.8312±0.0015 | 0.8312±0.0015 | 35.9 | 0.3692 | 30.27±8.93 |
| multiclass/RandomForest | 0.8297±0.0014 | 0.8297±0.0014 | 1039.2 | 0.0287 | n/a |

## ton_iot

Seeds: 7, 13, 19, 42, 123, 2024, 2025, 2026 · 190,474 rows after dedupe · 30 features · 10 classes

| task/model | macro-F1 (mean±sd) | F1 | size MB | infer ms | SHAP ms/alert |
|---|---|---|---|---|---|
| binary/LightGBM | 0.9969±0.0002 | 0.9987±0.0001 | 2.0 | 0.0249 | 3.50±0.52 |
| binary/RandomForest | 0.9970±0.0003 | 0.9987±0.0001 | 16.1 | 0.0106 | n/a |
| multiclass/LightGBM | 0.9543±0.0016 | 0.9543±0.0016 | 25.5 | 0.3213 | 30.34±4.67 |
| multiclass/RandomForest | 0.9533±0.0014 | 0.9533±0.0014 | 161.7 | 0.0216 | n/a |

## unsw_nb15

Seeds: 7, 13, 19, 42, 123, 2024, 2025, 2026 · 257,673 rows after dedupe · 42 features · 10 classes

| task/model | macro-F1 (mean±sd) | F1 | size MB | infer ms | SHAP ms/alert |
|---|---|---|---|---|---|
| binary/LightGBM | 0.9440±0.0010 | 0.9577±0.0008 | 2.0 | 0.0132 | 4.40±0.56 |
| binary/RandomForest | 0.9468±0.0011 | 0.9615±0.0008 | 276.3 | 0.0152 | n/a |
| multiclass/LightGBM | 0.5927±0.0077 | 0.5927±0.0077 | 26.4 | 0.2420 | 44.45±4.17 |
| multiclass/RandomForest | 0.5847±0.0091 | 0.5847±0.0091 | 1110.4 | 0.0317 | n/a |

## Read-out notes

- **H1:** Multi-class LightGBM ≈ RF everywhere; binary RF ahead on Edge (and slightly on UNSW).
- **H2:** Holds — multi-class LightGBM ~25–36 MB vs RF ~162–1110 MB (RF binaries not kept in git).
- **H3:** Multi-class SHAP ≫ binary, but not purely class-count driven (Edge 15 cls can be cheaper than UNSW 10).
- **H4:** Holds — ML-DSA-44 sign (~6.9 ms) dominates ML-KEM and IDS inference on this host.
- UNSW multi-class macro-F1 is rare-class sensitive; report per-class metrics in the paper.
- Eight-seed variance is tighter than the earlier three-seed estimates.
