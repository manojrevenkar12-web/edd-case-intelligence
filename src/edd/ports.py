"""What the workbench needs from a language model. Production: Claude through the Anthropic API or Bedrock
(`edd.claude.ClaudeDraftModel`). Evaluation: a simulated model whose behaviour is known."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from edd.prompts import PromptConfig


@dataclass
class Usage:
    input_tokens: int
    output_tokens: int
    latency_ms: float


class DraftModel(Protocol):
    def complete(self, system: str, user: str, cfg: PromptConfig, case_id: str) -> tuple[str, Usage]: ...
