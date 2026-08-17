"""
llm_gen/base.py
================
Shared types and the LLM-output parser used by every generator
implementation (mock, Qwen-local, or anything else you plug in later).

Design choice: the generator's JOB is to produce a raw text string (a
chat completion). Parsing that into structured AlphaIdea objects is
handled ONCE, here, so every generator implementation is consistent and
we don't duplicate fragile JSON-extraction logic three times.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import re


@dataclass
class AlphaIdea:
    """One candidate alpha expression proposed by the LLM."""
    expression: str
    rationale: str = ""


class AlphaIdeaGenerator(ABC):
    """
    Common interface every idea generator implements, so the
    orchestration loop (orchestrate.py) doesn't care whether it's
    talking to a mock, a local Qwen model, or an API-based model.
    """

    @abstractmethod
    def generate(self, n: int, feedback_context: str) -> list[AlphaIdea]:
        """
        Produce up to n new candidate alpha expressions.
        `feedback_context` is a text block (built by prompt_builder.py)
        summarizing what's worked and what hasn't so far -- this is how
        the loop gives the LLM in-context feedback each round.
        """
        raise NotImplementedError


class LLMOutputParseError(ValueError):
    """Raised when the LLM's raw text can't be turned into AlphaIdeas at all."""


def parse_llm_output(raw_text: str) -> list[AlphaIdea]:
    """
    Extract a JSON array of {"expression": ..., "rationale": ...} objects
    from raw LLM output text.

    LLMs are inconsistent about formatting -- they wrap JSON in markdown
    code fences, add a preamble sentence, etc. This function is
    deliberately lenient: it strips code fences, then finds the first
    balanced '[' ... ']' span and parses that, rather than requiring the
    ENTIRE response to be valid JSON.

    Returns an empty list (does not raise) if no valid ideas could be
    extracted at all -- malformed LLM output is an expected, common case
    the orchestration loop must handle gracefully, not a fatal error.
    """
    text = raw_text.strip()

    # strip ```json ... ``` or ``` ... ``` code fences if present
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    # find the first balanced top-level [...] span
    start = text.find("[")
    if start == -1:
        return []
    depth = 0
    end = None
    for i in range(start, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        return []

    json_str = text[start:end + 1]
    try:
        raw_items = json.loads(json_str)
    except json.JSONDecodeError:
        return []

    ideas = []
    for item in raw_items:
        if not isinstance(item, dict) or "expression" not in item:
            continue  # skip malformed individual entries rather than failing the whole batch
        ideas.append(AlphaIdea(
            expression=str(item["expression"]).strip(),
            rationale=str(item.get("rationale", "")).strip(),
        ))
    return ideas


def parse_single_llm_output(raw_text: str) -> AlphaIdea | None:
    """
    Like parse_llm_output, but extracts a single JSON OBJECT (not an
    array) -- used by ppo_finetune.py, where each PPO training example
    asks the model for exactly one alpha expression, so each generated
    completion must map to exactly one scalar reward.

    Returns None (not an exception) if nothing parseable was found --
    the PPO reward function treats that the same as an invalid expression.
    """
    text = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    end = None
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        return None

    try:
        item = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None

    if not isinstance(item, dict) or "expression" not in item:
        return None
    return AlphaIdea(
        expression=str(item["expression"]).strip(),
        rationale=str(item.get("rationale", "")).strip(),
    )


if __name__ == "__main__":
    # a handful of messy real-world-shaped LLM outputs to sanity check the parser
    cases = [
        '[{"expression": "rank(close)", "rationale": "simple momentum"}]',
        'Here are some ideas:\n```json\n[{"expression": "ts_delta(close, 5)", "rationale": "5-day change"}]\n```',
        '```\n[{"expression": "rank(volume)"}, {"expression": "ts_mean(returns, 10)", "rationale": "trend"}]\n```',
        'I cannot help with that.',                      # no JSON at all
        '[{"expression": "rank(close)", "rationale": "ok"}, {"not_expression": "bad"}]',  # one bad entry
        '[{"expression": "rank(close",]',                  # truncated/invalid JSON
    ]
    for c in cases:
        ideas = parse_llm_output(c)
        print(f"input={c[:50]!r:52s} -> {len(ideas)} idea(s): {ideas}")

    print("\nparse_single_llm_output cases:")
    single_cases = [
        '{"expression": "rank(close)", "rationale": "momentum"}',
        'Sure! ```json\n{"expression": "ts_delta(close, 5)"}\n```',
        'I refuse.',
        '{"expression": "rank(close)"',  # truncated
    ]
    for c in single_cases:
        idea = parse_single_llm_output(c)
        print(f"input={c[:50]!r:52s} -> {idea}")