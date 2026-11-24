# Devlog

## 24 Nov 2026

Ran the three-dataset, three-seed batch: ToN-IoT, UNSW-NB15 and Edge-IIoTset at seeds 42, 123 and 2024. Each seed now fixes both the train/test split and the model seed, so the spread across seeds reflects the split choice as well as model initialisation.

The first attempt deduplicated after replacing `-` placeholders and removed 117k ToN-IoT rows. The original audit removes 20,569, so dedupe now happens on raw rows before cleaning. Seed 42 then reproduced the earlier multi-class LightGBM macro-F1 (0.9542 against 0.9539).

UNSW-NB15 and Edge-IIoTset were not in the repo. Their official download endpoints need an interactive login, so I used Hugging Face copies whose row counts and columns match the documented releases; hashes are in `datasets/registry.json`.

Numbers are in `results/runs.csv` and `results/*/findings.json`. Model binaries and raw CSVs stay outside git. Next step is the Results section from those findings, plus a decision on whether to keep the roughly 1 GB multiclass random-forest artifacts.
