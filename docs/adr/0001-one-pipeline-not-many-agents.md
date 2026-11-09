# 1. One structured pipeline, not a chain of agents

**Context.** Wise's data scientists describe abandoning a multi-agent SAR system for a simpler pipeline: errors
compounded across agents, it was slow, expensive and hard to debug ("Scaling Fincrime Operations", wise.jobs).

**Decision.** One model call per case with a strict output schema, code before it (facts, computed indicators)
and code after it (evidence, numbers, risk floor, documents). Agentic behaviour lives where it pays: the case
workflow in LangGraph pauses for the analyst and acts only on approval.

**Consequences.** Every failure has one place to look. The pre-registered experiment E5 measured the value of
moving the arithmetic flags to code: +23 points of fully right cases on the held-out split.
