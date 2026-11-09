"""Drafts as the analyst sees them, and the analyst's final version. Plain text with labelled lines, so an edit
can be compared line by line."""

from __future__ import annotations

import re


def render(summary: str, flags: list[str], risk: str, documents: list[str]) -> str:
    return "\n".join(
        [
            f"Summary: {summary}",
            f"Red flags: {', '.join(sorted(flags)) or 'none'}",
            f"Risk: {risk}",
            f"Documents: {', '.join(sorted(documents)) or 'none'}",
        ]
    )


def render_final(draft_text: str, decision: dict) -> str:
    """The analyst's decision written over the draft's structured lines; the summary keeps its wording."""
    lines = draft_text.splitlines()
    summary = next((ln for ln in lines if ln.startswith("Summary: ")), "Summary: ")[len("Summary: ") :]
    return render(summary, decision["flags"], decision["risk"], decision["documents"])


def fields(text: str) -> dict:
    out = {}
    for ln in text.splitlines():
        if ":" in ln:
            k, v = ln.split(":", 1)
            out[k.strip()] = v.strip()
    out["numbers"] = sorted(re.findall(r"\d[\d,]*\.?\d*", out.get("Summary", "")))
    return out
