from edd.evals import Label
from edd.monitor import Monitor
from edd.pipeline import Draft
from edd.shadow import decide


def test_the_monitor_is_quiet_on_a_stable_stream_and_alerts_on_a_jump(records):
    m = Monitor(baseline_weeks=2)
    half = len(records) // 2
    for w in (1, 2):
        m.observe(w, records[:half], [set() for _ in records[:half]], ["factual"] * 6 + ["none"] * (half - 6))
    quiet = m.observe(
        3, records[half:], [set() for _ in records[half:]], ["factual"] * 6 + ["none"] * (len(records) - half - 6)
    )
    assert quiet.alerts == []
    loud = m.observe(
        4, records[half:], [set() for _ in records[half:]], ["factual"] * 40 + ["none"] * (len(records) - half - 40)
    )
    assert any("factual edits" in a for a in loud.alerts)


def test_shadow_promotes_only_a_candidate_that_is_not_worse_on_high_risk_cases():
    labels = {f"c{i}": Label(f"c{i}", set(), "high" if i % 3 == 0 else "low", set()) for i in range(600)}
    prod = [Draft(k, "draft", risk=v.risk if int(k[1:]) % 10 else "low") for k, v in labels.items()]
    better = [Draft(k, "draft", risk=v.risk) for k, v in labels.items()]
    worse = [Draft(k, "draft", risk="low") for k in labels]
    assert decide(prod, better, labels)["promote"]
    assert not decide(prod, worse, labels)["promote"]
    assert not decide(prod[:10], better[:10], labels)["promote"]
