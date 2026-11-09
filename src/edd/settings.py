"""Every threshold the workbench uses lives in config/edd.toml."""

from __future__ import annotations

import tomllib
from functools import cache

from edd.taxonomy import ROOT


@cache
def settings() -> dict:
    return tomllib.loads((ROOT / "config" / "edd.toml").read_text())
