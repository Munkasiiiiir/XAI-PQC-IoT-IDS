"""UNSW-NB15 adapter.

Expected raw files (place them yourself; not bundled):
  datasets/UNSW_NB15/UNSW_NB15_training-set.csv
  datasets/UNSW_NB15/UNSW_NB15_testing-set.csv
45 columns, columns include 'label' (0/1) and 'attack_cat' (Normal + 9 attacks).

Policy:
  - Concatenate train+test, clean placeholders, dedupe the UNION on full rows
    BEFORE splitting (the official split contains cross-boundary near-duplicates).
  - Drop identifier/leakage columns: id, srcip, sport, dstip, dsport.
  - Normalise attack_cat (strip, lower, plural fixes) -> 10 classes incl. normal.
  - Verify label polarity: attack_cat == 'normal' must be label 0.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

NAME = "unsw_nb15"
DISPLAY = "UNSW-NB15"
SOURCE_URL = "https://research.unsw.edu.au/projects/unsw-nb15-dataset"
LICENSE = "Free for academic research (cite Moustafa & Slay 2015, 2016)"

ROOT = Path(__file__).resolve().parents[2]
RAW_FILES = [
    ROOT / "datasets" / "UNSW_NB15" / "UNSW_NB15_training-set.csv",
    ROOT / "datasets" / "UNSW_NB15" / "UNSW_NB15_testing-set.csv",
]

DROP_EXACT = ["id", "srcip", "sport", "dstip", "dsport"]
TARGET_BINARY = "label"
TARGET_MULTI = "attack_cat"
LAST_DROPPED: list[str] = []
LAST_RAW_ROWS: int = 0
LAST_DEDUP_ROWS: int = 0

# Normalise the known messy spellings in attack_cat.
_MULTI_MAP = {
    "backdoors": "backdoor",
    "backdoor": "backdoor",
    "fuzzers": "fuzzers",
    "analysis": "analysis",
    "dos": "dos",
    "exploits": "exploits",
    "generic": "generic",
    "reconnaissance": "reconnaissance",
    "shellcode": "shellcode",
    "worms": "worms",
    "normal": "normal",
}


def missing_files() -> list[str]:
    return [str(p) for p in RAW_FILES if not p.exists()]


def build_frame() -> pd.DataFrame:
    global LAST_DROPPED
    missing = missing_files()
    if missing:
        raise FileNotFoundError(
            "Missing UNSW-NB15 raw file(s):\n  "
            + "\n  ".join(missing)
            + "\nDownload the 45-column CSVs named UNSW_NB15_training-set.csv and "
            "UNSW_NB15_testing-set.csv from the source URL and place them there."
        )

    frames = []
    for p in RAW_FILES:
        f = pd.read_csv(p, low_memory=False)
        frames.append(f)
    df = pd.concat(frames, ignore_index=True)
    global LAST_RAW_ROWS, LAST_DEDUP_ROWS
    LAST_RAW_ROWS = int(len(df))
    df = df.drop_duplicates().reset_index(drop=True)  # union dedupe BEFORE split
    LAST_DEDUP_ROWS = int(len(df))
    df = df.replace("-", pd.NA)

    for col in (TARGET_BINARY, TARGET_MULTI):
        if col not in df.columns:
            raise ValueError(
                f"UNSW-NB15 file missing expected column '{col}'. "
                f"Found columns: {list(df.columns)}"
            )

    y_bin = df[TARGET_BINARY].astype(int)
    raw_multi = df[TARGET_MULTI].astype(str).str.strip().str.lower()
    y_multi = raw_multi.map(lambda v: _MULTI_MAP.get(v, v))

    unknown = sorted(set(y_multi.unique()) - set(_MULTI_MAP.values()))
    if unknown:
        raise ValueError(f"Unexpected UNSW-NB15 attack_cat values after normalisation: {unknown}")

    normal_mask = y_multi == "normal"
    if (y_bin[normal_mask] != 0).any():
        raise ValueError(
            "UNSW-NB15 label polarity check failed: some attack_cat == 'normal' "
            "rows have label != 0. Refusing to train on an inconsistent target."
        )

    drop = [c for c in DROP_EXACT if c in df.columns]
    LAST_DROPPED = drop + [TARGET_BINARY, TARGET_MULTI]
    X = df.drop(columns=drop + [TARGET_BINARY, TARGET_MULTI], errors="ignore").copy()
    X["_y_bin"] = y_bin.to_numpy()
    X["_y_multi"] = y_multi.to_numpy()
    return X
