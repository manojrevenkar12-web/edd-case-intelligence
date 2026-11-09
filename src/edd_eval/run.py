"""The evaluation: labels, experiments, the held-out confirmation, the checks' value, twelve weeks of production
with a new typology, shadow mode, and upstream deflection. The only code that sees the world's truth."""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import replace

import numpy as np

from edd import deflection
from edd.agreement import adjudicate, agreement
from edd.edits import classify
from edd.evals import Label, evaluate, paired
from edd.experiments import Runner, baseline, run
from edd.monitor import Monitor
from edd.pipeline import draft
from edd.prompts import PromptConfig
from edd.render import render
from edd.settings import settings
from edd.shadow import decide
from edd_world.adapter import to_record
from edd_world.cases import TYPOLOGIES, sample_case
from edd_world.llm import SimulatedModel
from edd_world.people import analyst_review, annotate
from edd_world.population import becomes_high_risk_case, population


def cases(seed: int, n: int, week: int = 0, weights: dict | None = None):
    rng = np.random.default_rng(seed)
    return [sample_case(rng, f"s{seed}-w{week}-{i:04d}", week, weights=weights) for i in range(n)]


def labelled(cs) -> tuple[dict[str, Label], dict]:
    a = [annotate(c, "sme_a") for c in cs]
    b = [annotate(c, "sme_b") for c in cs]
    senior = {c.id: annotate(c, "senior") for c in cs}
    adj = adjudicate(a, b, senior)
    from edd.taxonomy import document_for

    labels = {
        k: Label(k, v.flags, v.risk, {document_for(f) for f in v.flags} if v.risk != "low" else set())
        for k, v in adj.items()
    }
    truth = {c.id: c for c in cs}
    label_errors = sum(labels[k].flags != truth[k].truth_flags or labels[k].risk != truth[k].truth_risk for k in labels)
    return labels, {**agreement(a, b), "adjudicated_label_error_rate": label_errors / len(cs)}


def stack(results: list[dict]) -> PromptConfig:
    """The production configuration chosen on the development split: every change that helped there."""
    cfg = baseline()
    for r in results:
        helped = r["confirmed"] and r["direction"] == "greater"
        if r["id"] == "E4-tool-schema":
            helped = r["confirmed"]
        if helped:
            cfg = replace(cfg, **r["change"])
    return cfg


def offline(which: str) -> dict:
    ev = settings()["evaluation"]
    seed = ev["seed_dev"] if which == "dev" else ev["seed_heldout"]
    cs = cases(seed, ev["dev_size"])
    labels, agree = labelled(cs)
    model = SimulatedModel({c.id: c for c in cs})
    runner = Runner([to_record(c) for c in cs], model)
    results = run(runner, labels)
    base = baseline()
    out = {"agreement": agree, "experiments": results}
    if which == "dev":
        chosen = stack(results)
    else:
        import json

        from edd.prompts import PromptConfig as P
        from edd.taxonomy import ROOT

        chosen = P(**json.loads((ROOT / "reports" / "dev.json").read_text())["chosen_config"])
    out["chosen_config"] = chosen.as_dict()
    final = runner.drafts(chosen)
    unchecked = [draft(c, model, chosen, checks=False) for c in runner.cases]
    out["baseline"] = evaluate(runner.drafts(base), labels)
    out["chosen"] = evaluate(final, labels)
    out["chosen_without_checks"] = evaluate(unchecked, labels)
    out["chosen_vs_baseline"] = paired(runner.drafts(base), final, labels, "case_correct")
    truth_labels = {c.id: Label(c.id, c.truth_flags, c.truth_risk, c.truth_documents) for c in cs}
    out["chosen_against_truth"] = evaluate(final, truth_labels)
    # the checks: what would have reached an analyst without them
    n = len(final)
    out["checks"] = {
        "unsupported_flags_dropped": sum(len(d.dropped) for d in final),
        "cases_with_unsupported_flag_without_checks": sum(
            any(f not in labels[d.case_id].flags for f in d.raw_flags) for d in final
        )
        / n,
        "cases_with_wrong_number_corrected": sum(bool(d.corrected_facts) for d in final) / n,
        "indicators_added": sum(len(d.added_indicators) for d in final),
        "risk_raised": sum(d.raised_risk for d in final),
    }
    return out


def production(chosen: PromptConfig) -> dict:
    ev = settings()["evaluation"]
    weights = {k: v[3] for k, v in TYPOLOGIES.items()}
    monitor = Monitor(settings()["monitor"]["baseline_weeks"])
    live = chosen
    candidate = replace(chosen, few_shot=max(3, chosen.few_shot), few_shot_set="v2")
    weeks, shadow_prod, shadow_cand, shadow_labels, promoted_at = [], [], [], {}, None
    for w in range(1, ev["weeks"] + 1):
        wts = dict(weights)
        if w >= ev["new_typology_week"]:
            wts["app_fraud_mule"] = 0.08
        cs = cases(5000 + w, ev["weekly_cases"], w, wts)
        model = SimulatedModel({c.id: c for c in cs})
        recs = [to_record(c) for c in cs]
        drafts = [draft(r, model, live) for r in recs]
        kinds, decisions = [], {}
        for c, d in zip(cs, drafts):
            before = render(d.summary, list(d.flags), d.risk, d.documents) if d.status == "draft" else ""
            after, dec = analyst_review(c, before or render("", [], "low", []))
            kinds.append(classify(before, after) if before else "factual")
            decisions[c.id] = Label(c.id, set(dec["flags"]), dec["risk"], set(dec["documents"]))
        rep = monitor.observe(w, recs, [set(d.flags) for d in drafts], kinds)
        quality = evaluate(drafts, decisions)
        if w in ev["shadow_weeks"]:
            shadow_prod += drafts
            shadow_cand += [draft(r, model, candidate) for r in recs]
            shadow_labels.update(decisions)
        serving = "candidate" if live == candidate else "production"
        gate = None
        if shadow_prod and w == max(ev["shadow_weeks"]):
            gate = decide(shadow_prod, shadow_cand, shadow_labels)
            if gate["promote"]:
                live, promoted_at = candidate, w + 1
        weeks.append(
            {
                **rep.to_dict(),
                "config": serving,
                "case_correct": quality["case_correct"],
                "high_risk_recall": quality["high_risk_recall"],
                "crypto_recall": quality["per_flag"]["crypto_offramp"]["recall"],
                "typologies": dict(Counter(c.typology for c in cs).most_common(3)),
                "gate": {k: gate[k] for k in ("promote", "reason", "high_risk", "case_correct")} if gate else None,
            }
        )
    first_alert = next((x["week"] for x in weeks if x["alerts"] and x["week"] >= ev["new_typology_week"]), None)
    false_alerts = sum(
        bool(x["alerts"])
        for x in weeks
        if settings()["monitor"]["baseline_weeks"] < x["week"] < ev["new_typology_week"]
    )
    return {
        "weeks": weeks,
        "first_alert_week": first_alert,
        "false_alert_weeks": false_alerts,
        "promoted_week": promoted_at,
        "candidate_config": candidate.as_dict(),
    }


def deflect() -> dict:
    pop = population(4242, 24000)
    recs = [to_record(c) for c in pop]
    y = np.array([becomes_high_risk_case(c) for c in pop])
    cut = 16000
    model = deflection.train(recs[:cut], y[:cut])
    s = model.score(recs[cut:])
    budgets = settings()["deflection"]["friction_budgets"]
    yt = y[cut:]
    from sklearn.metrics import roc_auc_score

    return {
        "customers": len(pop),
        "train": cut,
        "test": len(pop) - cut,
        "positives_test": int(yt.sum()),
        "auc": float(roc_auc_score(yt, s)),
        "auc_rules": float(roc_auc_score(yt, deflection.rule_baseline(recs[cut:]))),
        "model": deflection.policy_curve(s, yt, budgets),
        "rules": deflection.policy_curve(deflection.rule_baseline(recs[cut:]) + s * 1e-9, yt, budgets),
    }


def evaluate_all(which: str) -> dict:
    t0 = time.time()
    out = offline(which)
    if which == "dev":
        out["production"] = production(PromptConfig(**out["chosen_config"]))
        out["deflection"] = deflect()
    out["minutes"] = round((time.time() - t0) / 60, 1)
    return out
