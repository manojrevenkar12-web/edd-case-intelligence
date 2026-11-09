# AGENTS.md

How to work in this repository, for people and coding agents.

## Fast feedback

```bash
make lint        # ruff format --check and ruff check
make test        # all Python tests (seconds)
make web-test    # vitest for the dashboard
make lock-check  # the held-out lock still verifies
make dev         # labels, experiments, chosen configuration, 12 production weeks, deflection (under a minute)
make report      # RESULTS.md and web/public/data/dashboard.json from reports/*.json
make api         # FastAPI on :8000 (EDD_MODEL=claude for the Anthropic API)
```

## Invariants (tests enforce them)

1. **The workbench never sees the truth.** `edd_world` generates cases, people and a simulated model and keeps the
   truth; `edd_eval` scores against it. Nothing under `src/edd` imports either (`test_isolation.py`).
2. **The model reads; code checks; a person decides.** A flag reaches an analyst only with cited transfers that
   exist and show the pattern; every number is checked against the transfers; a lower risk than the flags imply
   needs a verified business (`test_pipeline.py`). Nothing contacts a customer before an analyst approves, and
   only with the documents the analyst approved (`test_workflow_and_adapters.py`).
3. **One taxonomy.** The prompt, the evidence checks, the labelling guideline and the eval harness read
   `config/taxonomy.yaml` and nothing else.
4. **Labels come from people.** Metrics are computed against the adjudicated labels of two SMEs and a senior
   reviewer, never against the model's own output.
5. **Settings in config.** Thresholds in `config/edd.toml`, prices in `config/prices.toml`, dashboard sizes and
   colours in `web/src/theme/tokens.ts`.
6. **Generated reports.** `RESULTS.md` and the dashboard data come from `scripts/report.py`.

## The held-out rule

The experiments in `experiments/registry.yaml` were written before any was run. They were estimated on the
development split; the production configuration was chosen there (`reports/dev.json`). Then every file that
decides the held-out result (workbench, world, evaluation, taxonomy, registry, config and the development report)
was pinned in `config/heldout.lock`, and `scripts/evaluate.py heldout` ran once. Changing any of those needs a new
held-out split.
