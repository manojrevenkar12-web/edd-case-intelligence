import math

import numpy as np

from edd.agreement import Annotation, adjudicate, agreement, cohen_kappa
from edd.evals import holm, wilson


def test_wilson_matches_published_values():
    lo, hi = wilson(81, 263)
    assert math.isclose(lo, 0.2553, abs_tol=5e-4) and math.isclose(hi, 0.3662, abs_tol=5e-4)


def test_holm_controls_the_family():
    assert holm([0.01, 0.04, 0.03, 0.2]) == [True, False, False, False]
    assert holm([0.001, 0.01, 0.02]) == [True, True, True]


def test_cohen_kappa_known_values():
    a = [1] * 20 + [0] * 15 + [1] * 5 + [0] * 10
    b = [1] * 20 + [0] * 15 + [0] * 5 + [1] * 10
    assert math.isclose(cohen_kappa(a, b), 0.4, abs_tol=1e-9)  # po 0.7, pe 0.5
    assert cohen_kappa([1, 0, 1], [1, 0, 1]) == 1.0


def test_agreement_and_adjudication():
    a = [Annotation("c1", "a", {"x"}, "high"), Annotation("c2", "a", set(), "low")]
    b = [Annotation("c1", "b", {"x"}, "high"), Annotation("c2", "b", {"x"}, "medium")]
    senior = {"c1": Annotation("c1", "s", {"x"}, "high"), "c2": Annotation("c2", "s", set(), "low")}
    assert agreement(a, b)["disagreements"] == 1
    adj = adjudicate(a, b, senior)
    assert adj["c2"].annotator == "s" and adj["c1"].annotator == "a"


def test_paired_comparison_finds_a_real_difference():
    from edd.evals import Label, paired
    from edd.pipeline import Draft

    labels = {f"c{i}": Label(f"c{i}", set(), "low", set()) for i in range(400)}
    rng = np.random.default_rng(0)
    a = [Draft(k, "draft", risk="low" if rng.random() < 0.6 else "high") for k in labels]
    b = [Draft(k, "draft", risk="low" if rng.random() < 0.8 else "high") for k in labels]
    r = paired(a, b, labels, "risk_correct")
    assert r["effect"] > 0.1 and r["ci"][0] > 0 and r["p"] < 0.01
