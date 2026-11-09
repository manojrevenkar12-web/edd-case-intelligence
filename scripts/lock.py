"""Pin everything that decides the held-out result before it runs: the workbench, the world, the evaluation,
the taxonomy, the pre-registered experiments and the configuration chosen on the development split.

python scripts/lock.py write    # once, after the development run
python scripts/lock.py verify   # scripts/evaluate.py heldout refuses to run unless this passes
"""

from __future__ import annotations

import hashlib
import sys

from edd.taxonomy import ROOT

PINNED = sorted(
    [
        *(ROOT / "src" / "edd").rglob("*.py"),
        *(ROOT / "src" / "edd_eval").rglob("*.py"),
        *(ROOT / "src" / "edd_world").rglob("*.py"),
        *(ROOT / "config").glob("*.toml"),
        ROOT / "config" / "taxonomy.yaml",
        ROOT / "experiments" / "registry.yaml",
        ROOT / "reports" / "dev.json",
    ]
)
LOCK = ROOT / "config" / "heldout.lock"


def lines() -> list[str]:
    return [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT)}" for p in PINNED]


def main(cmd: str) -> int:
    if cmd == "write":
        if LOCK.exists():
            sys.exit("config/heldout.lock exists; the held-out set is spent once it has been pinned")
        LOCK.write_text(
            "# sha256 of every file that decides a release, pinned before the held-out run\n"
            + "\n".join(lines())
            + "\n"
        )
        print(f"pinned {len(PINNED)} files")
        return 0
    want = [x for x in LOCK.read_text().splitlines() if x and not x.startswith("#")]
    got = lines()
    diff = sorted(set(want) ^ set(got))
    for d in diff:
        print("changed:", d)
    return 1 if diff else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "verify"))
