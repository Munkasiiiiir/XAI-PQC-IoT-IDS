"""ToN-IoT Network Train/Test adapter.

Raw: datasets/ToN_IoT/train_test_network.csv
Binary target: label (0 normal / 1 attack)
Multi target: type (10 classes incl. normal)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

NAME = "ton_iot"
DISPLAY = "ToN-IoT"
SOURCE_URL = "https://research.unsw.edu.au/projects/toniot-datasets"
LICENSE = "Academic research use (cite Alsaedi et al. 2020; Booij et al. 2022)"

ROOT = Path(__file__).resolve().parents[2]
RAW_FILES = [ROOT / "datasets" / "ToN_IoT" / "train_test_network.csv"]

# Identifier leakage + sparse high-cardinality text fields (same policy as the
# original single-seed pipeline).
DROP_EXACT = [
    "src_ip", "dst_ip", "src_port", "dst_port",
    "dns_query", "http_uri", "http_user_agent", "ssl_subject", "ssl_issuer",
    "http_orig_mime_types", "http_resp_mime_types", "weird_addl",
]

TARGET_BINARY = "label"
TARGET_MULTI = "type"
LAST_DROPPED: list[str] = []
LAST_RAW_ROWS: int = 0
LAST_DEDUP_ROWS: int = 0


def missing_files() -> list[str]:
    return [str(p) for p in RAW_FILES if not p.exists()]


def build_frame() -> pd.DataFrame:
    global LAST_DROPPED
    missing = missing_files()
    if missing:
        raise FileNotFoundError(f"Missing ToN-IoT raw file(s): {missing}")

    df = pd.concat([pd.read_csv(p, low_memory=False) for p in RAW_FILES], ignore_index=True)
    # Match the original pipeline: dedupe RAW rows (placeholders intact) BEFORE
    # cleaning, so '-' does not turn distinct flows into false duplicates.
    global LAST_RAW_ROWS, LAST_DEDUP_ROWS
    LAST_RAW_ROWS = int(len(df))
    df = df.drop_duplicates().reset_index(drop=True)
    LAST_DEDUP_ROWS = int(len(df))
    df = df.replace("-", pd.NA)

    y_bin = df[TARGET_BINARY].astype(int)
    y_multi = df[TARGET_MULTI].astype(str).str.strip().str.lower()

    drop = [c for c in DROP_EXACT if c in df.columns]
    LAST_DROPPED = drop + [TARGET_BINARY, TARGET_MULTI]
    X = df.drop(columns=drop + [TARGET_BINARY, TARGET_MULTI], errors="ignore").copy()
    X["_y_bin"] = y_bin.to_numpy()
    X["_y_multi"] = y_multi.to_numpy()
    return X
