#!/usr/bin/env python3
"""
Phase 2 — Preprocess ToN-IoT Network Train/Test CSV.

Actions:
  - Replace '-' placeholders
  - Drop leakage / identifier columns
  - Drop very sparse high-cardinality text fields (optional but recommended)
  - Encode categoricals with OrdinalEncoder (unknown-safe)
  - Remove exact duplicates
  - Stratified train/test split on multi-class `type`
  - Save processed artifacts + metadata

No hardware dependency. Software-only pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "datasets" / "ToN_IoT" / "train_test_network.csv"
OUT_DIR = ROOT / "artifacts" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
TEST_SIZE = 0.20

# Identifier leakage — must drop for realistic IDS evaluation
LEAKAGE_COLS = ["src_ip", "dst_ip", "src_port", "dst_port"]

# Sparse / high-cardinality text fields that add noise and weak generalization
DROP_SPARSE_TEXT = [
    "dns_query",
    "http_uri",
    "http_user_agent",
    "ssl_subject",
    "ssl_issuer",
    "http_orig_mime_types",
    "http_resp_mime_types",
    "weird_addl",
]

TARGET_BINARY = "label"
TARGET_MULTI = "type"


def load_raw(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


def clean_placeholders(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Official ToN-IoT uses '-' for missing categorical/text fields
    df = df.replace("-", np.nan)
    # Also normalize empty strings
    obj_cols = df.select_dtypes(include=["object"]).columns
    for c in obj_cols:
        df[c] = df[c].replace(r"^\s*$", np.nan, regex=True)
    return df


def select_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    drop_cols = [c for c in LEAKAGE_COLS + DROP_SPARSE_TEXT if c in df.columns]
    keep = [c for c in df.columns if c not in drop_cols]
    return df[keep].copy(), drop_cols


def split_features_targets(df: pd.DataFrame):
    y_bin = df[TARGET_BINARY].astype(int).copy()
    y_multi = df[TARGET_MULTI].astype(str).copy()
    X = df.drop(columns=[TARGET_BINARY, TARGET_MULTI])
    return X, y_bin, y_multi


def encode_features(X: pd.DataFrame):
    X = X.copy()
    cat_cols = X.select_dtypes(include=["object"]).columns.tolist()
    num_cols = [c for c in X.columns if c not in cat_cols]

    # Fill numeric NaNs with median
    for c in num_cols:
        median = X[c].median()
        X[c] = X[c].fillna(median)

    # Fill categorical NaNs then ordinal-encode (unknown_value for future safety)
    for c in cat_cols:
        X[c] = X[c].astype(str).fillna("missing")

    encoder = None
    if cat_cols:
        encoder = OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=-1,
        )
        X[cat_cols] = encoder.fit_transform(X[cat_cols])

    feature_names = X.columns.tolist()
    return X.astype(np.float64), feature_names, cat_cols, num_cols, encoder


def main() -> None:
    print(f"Loading: {RAW_CSV}")
    df = load_raw(RAW_CSV)
    print(f"Raw shape: {df.shape}")

    n_dup_before = int(df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"Dropped exact duplicates: {n_dup_before} → shape {df.shape}")

    df = clean_placeholders(df)
    df, dropped = select_columns(df)
    print(f"Dropped columns ({len(dropped)}): {dropped}")
    print(f"After column selection: {df.shape}")

    X, y_bin, y_multi = split_features_targets(df)

    # Stratify on multi-class type so rare classes (mitm) appear in both splits
    X_train, X_test, yb_train, yb_test, ym_train, ym_test = train_test_split(
        X,
        y_bin,
        y_multi,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y_multi,
    )

    # Fit encoders on TRAIN only
    X_train_enc, feature_names, cat_cols, num_cols, cat_encoder = encode_features(X_train)

    # Transform test with train statistics / encoder
    X_test_t = X_test.copy()
    for c in num_cols:
        median = X_train[c].median()
        X_test_t[c] = X_test_t[c].fillna(median)
    for c in cat_cols:
        X_test_t[c] = X_test_t[c].astype(str).fillna("missing")
    if cat_encoder is not None and cat_cols:
        X_test_t[cat_cols] = cat_encoder.transform(X_test_t[cat_cols])
    X_test_enc = X_test_t[feature_names].astype(np.float64)

    # Multi-class label encoding (fit on train labels only)
    le = LabelEncoder()
    ym_train_enc = le.fit_transform(ym_train)
    ym_test_enc = le.transform(ym_test)

    # Persist
    joblib.dump(
        {
            "X_train": X_train_enc,
            "X_test": X_test_enc,
            "y_bin_train": yb_train.to_numpy(),
            "y_bin_test": yb_test.to_numpy(),
            "y_multi_train": ym_train_enc,
            "y_multi_test": ym_test_enc,
            "feature_names": feature_names,
            "class_names": le.classes_.tolist(),
        },
        OUT_DIR / "toniot_network_splits.joblib",
    )

    # Also save CSVs for inspection
    train_out = X_train_enc.copy()
    train_out["label"] = yb_train.to_numpy()
    train_out["type"] = ym_train.to_numpy()
    train_out["type_id"] = ym_train_enc
    train_out.to_csv(OUT_DIR / "train.csv", index=False)

    test_out = X_test_enc.copy()
    test_out["label"] = yb_test.to_numpy()
    test_out["type"] = ym_test.to_numpy()
    test_out["type_id"] = ym_test_enc
    test_out.to_csv(OUT_DIR / "test.csv", index=False)

    if cat_encoder is not None:
        joblib.dump(cat_encoder, OUT_DIR / "ordinal_encoder.joblib")
    joblib.dump(le, OUT_DIR / "label_encoder_type.joblib")

    meta = {
        "raw_rows": int(pd.read_csv(RAW_CSV).shape[0]),
        "rows_after_dedup": int(df.shape[0]),
        "duplicates_removed": n_dup_before,
        "dropped_columns": dropped,
        "n_features": len(feature_names),
        "feature_names": feature_names,
        "categorical_features": cat_cols,
        "numeric_features": num_cols,
        "test_size": TEST_SIZE,
        "random_state": RANDOM_STATE,
        "train_rows": int(len(X_train_enc)),
        "test_rows": int(len(X_test_enc)),
        "binary_train_counts": {
            "0": int((yb_train == 0).sum()),
            "1": int((yb_train == 1).sum()),
        },
        "binary_test_counts": {
            "0": int((yb_test == 0).sum()),
            "1": int((yb_test == 1).sum()),
        },
        "multiclass_train_counts": {
            k: int(v) for k, v in ym_train.value_counts().to_dict().items()
        },
        "multiclass_test_counts": {
            k: int(v) for k, v in ym_test.value_counts().to_dict().items()
        },
        "class_names": le.classes_.tolist(),
    }
    (OUT_DIR / "preprocess_meta.json").write_text(json.dumps(meta, indent=2))

    print("\n=== Preprocessing complete ===")
    print(f"Features ({len(feature_names)}): {feature_names}")
    print(f"Train: {len(X_train_enc):,} | Test: {len(X_test_enc):,}")
    print(f"Classes: {le.classes_.tolist()}")
    print(f"Saved to: {OUT_DIR}")


if __name__ == "__main__":
    main()
