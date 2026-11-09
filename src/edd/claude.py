"""The production model port: Claude through the Anthropic Messages API (the same request works through Bedrock's
Anthropic endpoint). Structured output through a forced tool call when the configuration asks for it."""

from __future__ import annotations

import json
import time

from edd.ports import Usage
from edd.prompts import PromptConfig
from edd.schema import DraftOutput

MODEL_IDS = {"anthropic.claude-sonnet-4-5": "claude-sonnet-4-5", "anthropic.claude-haiku-4-5": "claude-haiku-4-5"}
TOOL = {"name": "edd_draft", "description": "Return the EDD draft.", "input_schema": DraftOutput.model_json_schema()}


class ClaudeDraftModel:
    def __init__(self, client, max_tokens: int = 1500):
        self.client = client  # anthropic.Anthropic() or anthropic.AnthropicBedrock()
        self.max_tokens = max_tokens

    def complete(self, system: str, user: str, cfg: PromptConfig, case_id: str) -> tuple[str, Usage]:
        req = {
            "model": MODEL_IDS[cfg.model],
            "max_tokens": self.max_tokens,
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            "messages": [{"role": "user", "content": user}],
            "metadata": {"user_id": f"edd-case-{case_id}"},
        }
        if cfg.output == "tool_schema":
            req["tools"] = [TOOL]
            req["tool_choice"] = {"type": "tool", "name": "edd_draft"}
        t0 = time.perf_counter()
        resp = self.client.messages.create(**req)
        ms = (time.perf_counter() - t0) * 1000
        if cfg.output == "tool_schema":
            block = next(b for b in resp.content if getattr(b, "type", "") == "tool_use")
            text = json.dumps(block.input)
        else:
            text = "".join(getattr(b, "text", "") for b in resp.content)
        return text, Usage(resp.usage.input_tokens, resp.usage.output_tokens, ms)
