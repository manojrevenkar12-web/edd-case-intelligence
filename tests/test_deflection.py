import numpy as np

from edd.deflection import policy_curve


def test_policy_curve_counts_what_each_friction_budget_catches():
    scores = np.array([0.9, 0.8, 0.7, 0.1, 0.2, 0.3, 0.05, 0.6])
    labels = np.array([1, 1, 0, 0, 0, 0, 0, 1])
    (r,) = policy_curve(scores, labels, [0.2])  # 1 of 5 good customers asked
    assert r["good_asked"] == 1 and r["caught"] == 2 and abs(r["recall"] - 2 / 3) < 1e-9  # 0.6 sits below the cut
