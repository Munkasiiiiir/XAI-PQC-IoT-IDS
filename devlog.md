# Devlog

## 24 Nov 2026

Ran the three-dataset, three-seed batch: ToN-IoT, UNSW-NB15 and Edge-IIoTset at seeds 42, 123 and 2024. Each seed now fixes both the train/test split and the model seed, so the spread across seeds reflects the split choice as well as model initialisation.

The first attempt deduplicated after replacing `-` placeholders and removed 117k ToN-IoT rows. The original audit removes 20,569, so dedupe now happens on raw rows before cleaning. Seed 42 then reproduced the earlier multi-class LightGBM macro-F1 (0.9542 against 0.9539).

UNSW-NB15 and Edge-IIoTset were not in the repo. Their official download endpoints need an interactive login, so I used Hugging Face copies whose row counts and columns match the documented releases; hashes are in `datasets/registry.json`.

Numbers are in `results/runs.csv` and `results/*/findings.json`. Model binaries and raw CSVs stay outside git. Next step is the Results section from those findings, plus a decision on whether to keep the roughly 1 GB multiclass random-forest artifacts.

## 25 Nov 2026

Kept eight seeds per dataset (42, 123, 2024, 7, 13, 19, 2025, 2026). The five new seeds came after reading the three-seed results, so they are logged in writing/preanalysis_extension.json with a separate hash. The frozen plan is unchanged and every run is reported.

Random Forest binaries used 8.1 GB and are reproducible from the raw CSV and seed, so they are removed after their size is written to the ledger. LightGBM binaries are kept. Ledger hash was the same before and after cleanup.

## 25 Nov 2026 - eight seeds and folder move

Added seeds 7, 13, 19, 2025 and 2026. There are now 96 run rows, eight per dataset. Macro-F1 for multiclass LightGBM is 0.9543 +/- 0.0016 on ToN-IoT, 0.5927 +/- 0.0077 on UNSW-NB15 and 0.8312 +/- 0.0015 on Edge-IIoTset. The variance estimate is tighter than with three seeds.

The project now sits in C:\Users\YourName\Documents\Papers\paper 6\XAI-PQC-IoT-IDS. Random Forest binaries are not kept; their sizes and all metrics are in results/runs.csv.
