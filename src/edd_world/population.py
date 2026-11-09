"""All new customers in a period, not only the ones that became EDD cases (truth side). Most are ordinary; a few
percent follow a suspicious typology and, if nothing stops them, become high-risk EDD cases weeks later."""

from __future__ import annotations

import numpy as np

from edd_world.cases import TYPOLOGIES, Case, sample_case


def population(seed: int, n: int) -> list[Case]:
    rng = np.random.default_rng(seed)
    weights = {k: v[3] * (0.12 if v[0] else 1.0) for k, v in TYPOLOGIES.items()}
    return [sample_case(rng, f"p{seed}-{i:05d}", 0, weights=weights) for i in range(n)]


def becomes_high_risk_case(c: Case) -> int:
    return int(TYPOLOGIES[c.typology][0] and c.truth_risk == "high")
