"""Edge-IIoTset adapter (ML/DL-ready CSV from the Kaggle/IEEE DataPort release).

Expected raw file (place it yourself; not bundled), one of:
  datasets/Edge_IIoTset/DNN-EdgeIIoT-dataset.csv
  datasets/Edge_IIoTset/DNN-IIoTset-dataset.csv
  datasets/Edge_IIoTset/ML-EdgeIIoT-dataset.csv

Policy:
  - Drop the identifier/leakage columns listed in the dataset's own
    preprocessing instructions plus host/port/URI/payload/topic fields.
  - Targets: Attack_label (binary) and Attack_type (multi-class).
  - Verify polarity using Attack_type == normal; flip only if systematically
    inverted, otherwise refuse.
  - Dedupe happens later, in the harness, before splitting.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

NAME = "edge_iiot"
DISPLAY = "Edge-IIoTset"
SOURCE_URL = "https://ieee-dataport.org/documents/edge-iiotset-new-comprehensive-realistic-cyber-security-dataset-iot-and-iiot-applications"
LICENSE = "CC BY 4.0 (free for academic research; cite Ferrag et al. 2022)"

ROOT = Path(__file__).resolve().parents[2]
RAW_CANDIDATES = [
    ROOT / "datasets" / "Edge_IIoTset" / "DNN-EdgeIIoT-dataset.csv",
    ROOT / "datasets" / "Edge_IIoTset" / "DNN-IIoTset-dataset.csv",
    ROOT / "datasets" / "Edge_IIoTset" / "ML-EdgeIIoT-dataset.csv",
]

# Alias so the shared registry code can enumerate raw files uniformly.
RAW_FILES = RAW_CANDIDATES

# Identifier / leakage columns: from the dataset's official preprocessing list
# plus additional host/port/URI/topic fields that can leak scenario identity.
DROP_EXACT = [
    "frame.time", "frame.number",
    "ip.src_host", "ip.dst_host",
    "arp.src.proto_ipv4", "arp.dst.proto_ipv4",
    "http.file_data", "http.request.full_uri", "http.request.uri.query",
    "http.uri", "http.file",
    "icmp.transmit_timestamp",
    "tcp.options", "tcp.payload", "tcp.srcport", "tcp.dstport",
    "udp.port",
    "dns.query", "dns.qry.name",
    "mqtt.msg", "mqtt.topic",
]

# Any remaining column matching these patterns is dropped too.
DROP_REGEX = [
    r"^frame\.",
    r"^ip\.src_host$",
    r"^ip\.dst_host$",
    r"^arp\.",
]

_BINARY_CANDIDATES = ["attack_label", "attacklabel", "label"]
_MULTI_CANDIDATES = ["attack_type", "attacktype", "type"]

_NORMAL_TOKENS = {"normal", "benign", "0"}
# Declared target names (the adapter resolves the actual columns case-insensitively).
TARGET_BINARY = "Attack_label"
TARGET_MULTI = "Attack_type"
LAST_DROPPED: list[str] = []
LAST_RAW_ROWS: int = 0
LAST_DEDUP_ROWS: int = 0


def missing_files() -> list[str]:
    if any(p.exists() for p in RAW_CANDIDATES):
        return []
    return [str(RAW_CANDIDATES[0])]


def _resolve_raw() -> Path:
    for p in RAW_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError(
        "Missing Edge-IIoTset raw CSV. Expected one of:\n  "
        + "\n  ".join(str(p) for p in RAW_CANDIDATES)
        + "\nDownload DNN-EdgeIIoT-dataset.csv from the Kaggle/IEEE DataPort "
        "release and place it there."
    )


def _find_col(columns, candidates):
    lower = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand in lower:
            return lower[cand]
    return None


def build_frame() -> pd.DataFrame:
    global LAST_DROPPED
    raw = _resolve_raw()
    df = pd.read_csv(raw, low_memory=False)
    global LAST_RAW_ROWS, LAST_DEDUP_ROWS
    LAST_RAW_ROWS = int(len(df))
    df = df.drop_duplicates().reset_index(drop=True)  # dedupe BEFORE split
    LAST_DEDUP_ROWS = int(len(df))
    df = df.replace("-", pd.NA)

    bin_col = _find_col(df.columns, _BINARY_CANDIDATES)
    multi_col = _find_col(df.columns, _MULTI_CANDIDATES)
    if multi_col is None:
        raise ValueError(
            f"Edge-IIoTset file missing an attack-type label column. "
            f"Columns: {list(df.columns)}"
        )

    y_multi = (
        df[multi_col].astype(str).str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
    )
    normal_mask = y_multi.isin(_NORMAL_TOKENS)

    if bin_col is not None:
        y_bin = pd.to_numeric(df[bin_col], errors="coerce")
        if y_bin.isna().any():
            raise ValueError(f"Edge-IIoTset binary label column '{bin_col}' has non-numeric values.")
        y_bin = y_bin.astype(int)
        # Polarity check: normal rows must be 0. If systematically inverted, flip.
        if (y_bin[normal_mask] == 1).mean() > 0.99:
            y_bin = 1 - y_bin
        if (y_bin[normal_mask] != 0).any():
            raise ValueError(
                "Edge-IIoTset label polarity check failed: some normal rows have "
                "Attack_label != 0 even after inversion test."
            )
    else:
        y_bin = (~normal_mask).astype(int)

    drop = [c for c in DROP_EXACT if c in df.columns]
    regex = re.compile("|".join(DROP_REGEX))
    drop += [c for c in df.columns if regex.search(c) and c not in drop]

    LAST_DROPPED = drop + [c for c in [bin_col, multi_col] if c]
    X = df.drop(columns=drop + [bin_col, multi_col], errors="ignore").copy()
    X["_y_bin"] = y_bin.to_numpy()
    X["_y_multi"] = y_multi.to_numpy()
    return X
