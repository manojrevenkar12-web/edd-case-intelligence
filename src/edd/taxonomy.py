"""The labelling taxonomy, loaded once from config/taxonomy.yaml."""

from __future__ import annotations

from functools import cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


@cache
def taxonomy() -> dict:
    return yaml.safe_load((ROOT / "config" / "taxonomy.yaml").read_text())


def flag_names() -> list[str]:
    return list(taxonomy()["flags"])


def document_for(flag: str) -> str:
    return taxonomy()["flags"][flag]["document"]


def risk_from(flags: set[str], declared: str, documents_on_file: bool, mitigation_map: dict[str, str]) -> str:
    """The taxonomy's risk rule, for drafts that state flags and the context the reviewer verified."""
    t = taxonomy()
    who = mitigation_map.get(declared)
    mitigated = set(t["risk"]["mitigations"].get(who, [])) if who and documents_on_file else set()
    score = sum(t["flags"][f]["severity"] for f in flags if f not in mitigated)
    if score >= t["risk"]["high_at"]:
        return "high"
    return "medium" if score >= t["risk"]["medium_at"] else "low"
