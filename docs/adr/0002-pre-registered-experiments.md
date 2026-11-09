# 2. Prompt changes are pre-registered experiments

**Context.** Prompt tweaks tried one at a time on a handful of cases find "improvements" that are noise, and an
evaluation set used to choose a prompt cannot also measure it.

**Decision.** Each change is a hypothesis in `experiments/registry.yaml` with its metric and direction, written
before it runs. Effects are paired, case by case, with bootstrap intervals. The development split picks; the
held-out split, pinned by a lock, tests the family once with a Holm correction.

**Consequences.** Two of seven hypotheses held on the held-out split. More worked examples and putting computed
facts first, which a quick look would have kept, did not.
