"""Token cost at list prices (config/prices.toml)."""

from __future__ import annotations

import tomllib
from functools import cache

from edd.taxonomy import ROOT


@cache
def prices() -> dict:
    return tomllib.loads((ROOT / "config" / "prices.toml").read_text())


def usd(model: str, input_tokens: float, output_tokens: float) -> float:
    p = prices()[model]
    return (input_tokens * p["input_per_mtok"] + output_tokens * p["output_per_mtok"]) / 1e6
