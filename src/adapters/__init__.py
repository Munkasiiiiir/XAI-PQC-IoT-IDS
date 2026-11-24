"""Dataset adapter registry.

Each adapter module exposes:
  NAME, DISPLAY, SOURCE_URL, LICENSE, RAW_FILES
  build_frame() -> pandas.DataFrame with feature columns plus
                   reserved columns "_y_bin" (int) and "_y_multi" (str),
                   placeholders already cleaned and identifier/leakage
                   columns already dropped.
"""

from __future__ import annotations

import importlib

_REGISTRY = {
    "ton_iot": "adapters.ton_iot",
    "unsw_nb15": "adapters.unsw_nb15",
    "edge_iiot": "adapters.edge_iiot",
}

ALIASES = {
    "toniot": "ton_iot",
    "ton-iot": "ton_iot",
    "ton": "ton_iot",
    "unsw": "unsw_nb15",
    "unsw-nb15": "unsw_nb15",
    "nb15": "unsw_nb15",
    "edge": "edge_iiot",
    "edge-iiot": "edge_iiot",
    "edge-iiotset": "edge_iiot",
    "iiot": "edge_iiot",
}


def available() -> list[str]:
    return list(_REGISTRY)


def get_adapter(name: str):
    key = ALIASES.get(name.lower(), name.lower())
    if key not in _REGISTRY:
        raise KeyError(
            f"Unknown dataset '{name}'. Available: {sorted(_REGISTRY)} "
            f"(aliases: {sorted(ALIASES)})"
        )
    return importlib.import_module(_REGISTRY[key])
