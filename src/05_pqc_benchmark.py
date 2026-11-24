#!/usr/bin/env python3
"""
Phase 5 — Software-only PQC microbenchmarks.

Algorithms:
  - ML-KEM-512 / 768 / 1024  (NIST Kyber family)
  - ML-DSA-44 / 65 / 87      (NIST Dilithium family)

Also reports classical ECDH (P-256) + ECDSA (P-256) baselines via `cryptography`.

No Raspberry Pi / ESP32 claims. Host-PC software timings only.
"""

from __future__ import annotations

import importlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

N_ITERS = 100
WARMUP = 10


def bench(fn, iters: int = N_ITERS, warmup: int = WARMUP):
    for _ in range(warmup):
        fn()
    times = []
    out = None
    for _ in range(iters):
        t0 = time.perf_counter()
        out = fn()
        times.append(time.perf_counter() - t0)
    arr = np.array(times)
    return out, float(arr.mean()), float(arr.std()), float(arr.min()), float(arr.max())


def benchmark_kem(module_name: str) -> dict:
    mod = importlib.import_module(f"pqcrypto.kem.{module_name}")
    _, keygen_mean, keygen_std, _, _ = bench(lambda: mod.keygen())
    pk, sk = mod.keygen()

    def encaps():
        return mod.encaps(pk)

    _, enc_mean, enc_std, _, _ = bench(encaps)
    ct, ss = mod.encaps(pk)

    def decaps():
        return mod.decaps(sk, ct)

    _, dec_mean, dec_std, _, _ = bench(decaps)
    ss2 = mod.decaps(sk, ct)
    assert ss == ss2

    return {
        "family": "ML-KEM",
        "algorithm": module_name,
        "public_key_bytes": int(mod.PUBLIC_KEY_SIZE),
        "secret_key_bytes": int(mod.SECRET_KEY_SIZE),
        "ciphertext_bytes": int(mod.CIPHERTEXT_SIZE),
        "shared_secret_bytes": int(mod.SHARED_SECRET_SIZE),
        "signature_bytes": None,
        "keygen_ms": round(keygen_mean * 1000, 4),
        "keygen_std_ms": round(keygen_std * 1000, 4),
        "encaps_or_sign_ms": round(enc_mean * 1000, 4),
        "encaps_or_sign_std_ms": round(enc_std * 1000, 4),
        "decaps_or_verify_ms": round(dec_mean * 1000, 4),
        "decaps_or_verify_std_ms": round(dec_std * 1000, 4),
        "iters": N_ITERS,
    }


def benchmark_dsa(module_name: str, message: bytes = b"toniot-pqc-benchmark") -> dict:
    mod = importlib.import_module(f"pqcrypto.sign.{module_name}")
    _, keygen_mean, keygen_std, _, _ = bench(lambda: mod.keygen())
    pk, sk = mod.keygen()

    def sign():
        return mod.sign(sk, message)

    _, sign_mean, sign_std, _, _ = bench(sign)
    sig = mod.sign(sk, message)

    def verify():
        return mod.verify(pk, message, sig)

    _, ver_mean, ver_std, _, _ = bench(verify)
    # pqcrypto verify returns None on success; raises/fails otherwise
    mod.verify(pk, message, sig)

    return {
        "family": "ML-DSA",
        "algorithm": module_name,
        "public_key_bytes": int(mod.PUBLIC_KEY_SIZE),
        "secret_key_bytes": int(mod.SECRET_KEY_SIZE),
        "ciphertext_bytes": None,
        "shared_secret_bytes": None,
        "signature_bytes": int(mod.SIGNATURE_SIZE),
        "keygen_ms": round(keygen_mean * 1000, 4),
        "keygen_std_ms": round(keygen_std * 1000, 4),
        "encaps_or_sign_ms": round(sign_mean * 1000, 4),
        "encaps_or_sign_std_ms": round(sign_std * 1000, 4),
        "decaps_or_verify_ms": round(ver_mean * 1000, 4),
        "decaps_or_verify_std_ms": round(ver_std * 1000, 4),
        "iters": N_ITERS,
    }


def benchmark_classical() -> list[dict]:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.ec import ECDH

    rows = []

    # ECDH P-256
    def ecdh_keygen():
        return ec.generate_private_key(ec.SECP256R1())

    _, kg_mean, kg_std, _, _ = bench(ecdh_keygen)
    priv_a = ec.generate_private_key(ec.SECP256R1())
    priv_b = ec.generate_private_key(ec.SECP256R1())
    pub_b = priv_b.public_key()

    def ecdh_exchange():
        return priv_a.exchange(ECDH(), pub_b)

    _, ex_mean, ex_std, _, _ = bench(ecdh_exchange)
    shared = priv_a.exchange(ECDH(), pub_b)

    rows.append(
        {
            "family": "Classical",
            "algorithm": "ECDH_P256",
            "public_key_bytes": 65,  # uncompressed point approx
            "secret_key_bytes": 32,
            "ciphertext_bytes": None,
            "shared_secret_bytes": len(shared),
            "signature_bytes": None,
            "keygen_ms": round(kg_mean * 1000, 4),
            "keygen_std_ms": round(kg_std * 1000, 4),
            "encaps_or_sign_ms": round(ex_mean * 1000, 4),
            "encaps_or_sign_std_ms": round(ex_std * 1000, 4),
            "decaps_or_verify_ms": None,  # exchange is one-sided here
            "decaps_or_verify_std_ms": None,
            "iters": N_ITERS,
            "notes": "encaps_or_sign_ms = ECDH exchange time",
        }
    )

    # ECDSA P-256
    def ecdsa_keygen():
        return ec.generate_private_key(ec.SECP256R1())

    _, kg2_mean, kg2_std, _, _ = bench(ecdsa_keygen)
    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key()
    msg = b"toniot-pqc-benchmark"

    def ecdsa_sign():
        return priv.sign(msg, ec.ECDSA(hashes.SHA256()))

    _, sign_mean, sign_std, _, _ = bench(ecdsa_sign)
    signature = priv.sign(msg, ec.ECDSA(hashes.SHA256()))

    def ecdsa_verify():
        pub.verify(signature, msg, ec.ECDSA(hashes.SHA256()))
        return True

    _, ver_mean, ver_std, _, _ = bench(ecdsa_verify)

    rows.append(
        {
            "family": "Classical",
            "algorithm": "ECDSA_P256",
            "public_key_bytes": 65,
            "secret_key_bytes": 32,
            "ciphertext_bytes": None,
            "shared_secret_bytes": None,
            "signature_bytes": len(signature),
            "keygen_ms": round(kg2_mean * 1000, 4),
            "keygen_std_ms": round(kg2_std * 1000, 4),
            "encaps_or_sign_ms": round(sign_mean * 1000, 4),
            "encaps_or_sign_std_ms": round(sign_std * 1000, 4),
            "decaps_or_verify_ms": round(ver_mean * 1000, 4),
            "decaps_or_verify_std_ms": round(ver_std * 1000, 4),
            "iters": N_ITERS,
            "notes": "signature_bytes varies (DER encoding)",
        }
    )
    return rows


def main():
    rows = []
    print("Benchmarking ML-KEM...")
    for name in ["ml_kem_512", "ml_kem_768", "ml_kem_1024"]:
        row = benchmark_kem(name)
        rows.append(row)
        print(json.dumps(row, indent=2))

    print("\nBenchmarking ML-DSA...")
    for name in ["ml_dsa_44", "ml_dsa_65", "ml_dsa_87"]:
        row = benchmark_dsa(name)
        rows.append(row)
        print(json.dumps(row, indent=2))

    print("\nBenchmarking classical baselines...")
    classical = benchmark_classical()
    rows.extend(classical)
    for row in classical:
        print(json.dumps(row, indent=2))

    df = pd.DataFrame(rows)
    out = RESULT_DIR / "pqc_benchmarks.csv"
    df.to_csv(out, index=False)

    meta = {
        "environment": "host_pc_software_only",
        "hardware_claims": "none",
        "library": "pqcrypto + cryptography",
        "iterations": N_ITERS,
        "warmup": WARMUP,
        "note": "Timings are for local software evaluation only; not Raspberry Pi/ESP32 results.",
    }
    (RESULT_DIR / "pqc_benchmarks_meta.json").write_text(json.dumps(meta, indent=2))

    print("\n=== Phase 5 complete ===")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
