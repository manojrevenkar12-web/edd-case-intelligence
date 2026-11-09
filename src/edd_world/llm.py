"""A simulated foundation model for EDD drafts (truth side).

How often it finds each flag, invents evidence or a number, ignores a mitigating context, or breaks the output
format depends on the prompt configuration in hidden ways, the way a real model's does. The workbench sees only
the text it returns and the token usage, as it would from the API.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

from edd.ports import Usage
from edd.prompts import PromptConfig
from edd_world.cases import NEW_EXCHANGES, Case
from edd_world.truth import TAXONOMY, risk_of

FLAGS = list(TAXONOMY["flags"])
COMPUTED = {"structuring", "pass_through", "high_velocity_inbound", "funnel_outbound", "high_risk_jurisdiction"}
RARE = {"funnel_outbound", "crypto_offramp", "structuring"}
_BASE = {"anthropic.claude-sonnet-4-5": 0.86, "anthropic.claude-haiku-4-5": 0.80}
_MITIGATION = {"anthropic.claude-sonnet-4-5": 0.80, "anthropic.claude-haiku-4-5": 0.62}


def _u(*parts: object) -> float:
    h = hashlib.blake2b("|".join(map(str, parts)).encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") / 2**64


class SimulatedModel:
    def __init__(self, cases: dict[str, Case]):
        self.cases = cases

    def _p_detect(self, c: Case, flag: str, cfg: PromptConfig) -> float:
        p = _BASE[cfg.model]
        n = len(c.transfers)
        lost = {"raw": 0.0022, "chronological": 0.0012, "aggregated_first": 0.0004}[cfg.context_order]
        p -= lost * max(0, n - 40)  # long histories bury the pattern
        if flag in RARE:
            p += {0: -0.08, 3: 0.02, 8: 0.05}[cfg.few_shot]
        if cfg.cot:
            p += 0.02
        if flag == "crypto_offramp" and any(t.counterparty in NEW_EXCHANGES for t in c.transfers):
            p = 0.30 if cfg.few_shot_set == "v1" or cfg.few_shot == 0 else p - 0.03
        return float(np.clip(p, 0.05, 0.99))

    def _p_false(self, c: Case, flag: str, cfg: PromptConfig) -> float:
        p = 0.035 if flag not in ("profile_mismatch",) else 0.07
        if cfg.cot:
            p *= 0.6
        if cfg.few_shot >= 3:
            p *= 0.8
        return p

    def complete(self, system: str, user: str, cfg: PromptConfig, case_id: str) -> tuple[str, Usage]:
        c = self.cases[case_id]
        k = cfg.key()
        ids = [t.id for t in c.transfers]
        flags: list[dict] = []
        given = {}
        if cfg.indicators:
            for line in user.splitlines():
                if line.startswith("Computed indicators"):
                    given = json.loads(line.split(": ", 1)[1])
        hall = {"raw": 0.07, "chronological": 0.05, "aggregated_first": 0.03}[cfg.context_order]
        hall *= 0.5 if cfg.output == "tool_schema" else 1.0
        for f in FLAGS:
            if cfg.indicators and f in COMPUTED:
                if f in given:
                    flags.append({"flag": f, "evidence": given[f], "rationale": "computed"})
                continue
            present = f in c.truth_flags
            p = self._p_detect(c, f, cfg) if present else self._p_false(c, f, cfg)
            if _u(c.id, k, f, "detect") < p:
                if present and _u(c.id, k, f, "hall") > hall:
                    ev = self._evidence(c, f)
                else:
                    ev = [ids[int(_u(c.id, k, f, j) * len(ids))] for j in range(2)]
                    if _u(c.id, k, f, "ghost") < 0.5:
                        ev[0] = f"{c.id}-t{900 + int(_u(c.id, f) * 99)}"  # an id that does not exist
                flags.append({"flag": f, "evidence": ev, "rationale": f"pattern for {f}"})
        stated = {x["flag"] for x in flags}
        # Risk: the taxonomy rule, applied with or without the customer's mitigating context.
        mit = _MITIGATION[cfg.model] + (0.08 if cfg.cot else 0.0) + (0.04 if cfg.few_shot >= 3 else 0.0)
        if _u(c.id, k, "mit") < mit:
            risk = risk_of(stated, c)
        else:
            risk = risk_of(stated, Case(**{**c.__dict__, "declared": "unknown"}))
        docs = sorted({TAXONOMY["flags"][f]["document"] for f in stated}) if risk != "low" else []
        f = self._facts(c)
        p_fact = {"raw": 0.09, "chronological": 0.07, "aggregated_first": 0.015}[cfg.context_order] * (
            0.7 if cfg.cot else 1
        )
        if _u(c.id, k, "fact") < p_fact:
            key = ["total_in_eur", "total_out_eur", "transfers"][int(_u(c.id, k, "which") * 3)]
            f[key] = round(f[key] * (1.1 + _u(c.id, "x")), 2) if key != "transfers" else f[key] + 7
        out = {
            "summary": f"{c.kind.title()} customer, declared '{c.declared}'. Received EUR {f['total_in_eur']:,.2f} "
            f"and sent EUR {f['total_out_eur']:,.2f} across {f['transfers']} transfers; largest "
            f"counterparty {f['largest_counterparty']}.",
            "facts": f,
            "flags": flags,
            "risk": risk,
            "documents": docs,
        }
        text = json.dumps(out)
        p_fmt = {"json_text": 0.05, "tool_schema": 0.004}[cfg.output] + (
            0.02 if cfg.cot and cfg.output == "json_text" else 0
        )
        if _u(c.id, k, "fmt", len(user)) < p_fmt:
            text = "Here is the draft:\n" + text[: int(len(text) * 0.8)]
        n = len(c.transfers)
        inp = 1200 + 380 + (13 * n if cfg.context_order != "aggregated_first" else 13 * n + 60) + cfg.few_shot * 900
        if cfg.indicators:
            inp += 150
        outp = 380 + (520 if cfg.cot else 0)
        speed = 6.0 if "sonnet" in cfg.model else 3.5
        lat = 600 + inp * 0.05 + outp * speed
        return text, Usage(inp, outp, lat)

    def _evidence(self, c: Case, f: str) -> list[str]:
        from edd.features import indicators
        from edd_world.adapter import to_record

        found = {i.flag: i.evidence for i in indicators(to_record(c))}
        if f in found:
            return found[f]
        if f == "crypto_offramp":
            outs = [t.id for t in c.transfers if t.direction == "out" and t.reference == "top up"]
            return outs[:4] or [c.transfers[0].id]
        return [c.transfers[0].id]

    @staticmethod
    def _facts(c: Case) -> dict:
        from collections import defaultdict

        by = defaultdict(float)
        for t in c.transfers:
            by[t.counterparty] += t.amount_eur
        return {
            "total_in_eur": round(sum(t.amount_eur for t in c.transfers if t.direction == "in"), 2),
            "total_out_eur": round(sum(t.amount_eur for t in c.transfers if t.direction == "out"), 2),
            "transfers": len(c.transfers),
            "largest_counterparty": max(by, key=by.get),
        }
