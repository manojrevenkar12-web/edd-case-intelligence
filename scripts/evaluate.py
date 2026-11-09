"""python scripts/evaluate.py dev | heldout

dev: labels, experiments, the chosen configuration, twelve production weeks with shadow mode, deflection.
heldout: the pre-registered experiments and the chosen configuration on new cases, once, after the lock."""

from __future__ import annotations

import json
import subprocess
import sys

from edd.taxonomy import ROOT
from edd_eval.run import evaluate_all


def main(which: str) -> None:
    out = ROOT / "reports" / f"{which}.json"
    if which == "heldout":
        if out.exists():
            sys.exit("reports/heldout.json exists: the held-out split is tested once.")
        if subprocess.run([sys.executable, str(ROOT / "scripts" / "lock.py"), "verify"]).returncode:
            sys.exit("config/heldout.lock does not verify")
    rep = evaluate_all(which)
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rep, indent=1, default=lambda o: sorted(o) if isinstance(o, set) else float(o)))
    print(json.dumps({k: rep[k] for k in ("chosen_config", "minutes")}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dev")
