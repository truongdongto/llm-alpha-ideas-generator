"""
llm_gen/base.py
================
Shared types and the LLM-output parser used by every generator implementation.
Parse a raw text string (a chat completion) into structured AlphaIdea objects.
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
    Common interface every idea generator implements.
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
    Extract a JSON array of {"expression": ..., "rationales": ...} objects
    from raw LLM output text.

    Returns an empty list if no valid ideas could be extracted.
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
    array) -- used by ppo_finetune.py.

    Returns None (not an exception) if nothing parseable was found/
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
    response = """[{"expression": "(-1 * ((rank(((((high + low + close) / 3) - (sum(((high + low + close) / 3), 2) / 2))) / (0.015 * (sum(abs(((high + low + close) / 3) - (sum(((high + low + close) / 3), 2) / 2)), 2) / sum(abs(((high + low + close) / 3) - (sum(((high + low + close) / 3), 2) / 2)), 2)))) * (1 - rank(((((high + low + close) / 3) - (sum(((high + low + close) / 3), 2) / 2)) / (0.015 * (sum(abs(((high + low + close) / 3) - (sum(((high + low + close) / 3), 2) / 2)), 2) / sum(abs(((high + low + close) / 3) - (sum(((high + low + close) / 3), 2) / 2)), 2)))))))", "rationale": "A volume-based predictive signal utilizing volume metrics, cross-sectional ranking, historical time-series averages, rescaled inputs, rolling minimums to capture changes in trading intensity and capital flow across assets."}, {"expression": "(-1 * (0.001 * (((1 - rank((0.001 * sum((returns * volume), 10)))) - (1 - rank(0.001 * sum((returns * volume), 1)))) / (0.001 * sum((returns * volume), 10))))", "rationale": "A volume-based predictive signal utilizing volume metrics, historical returns, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."}, {"expression": "(-1 * rank(((((high - close) / (high - low)) - 0.5) / (0.5 * (1 - abs((high - close) / (high - low))))) * volume)))", "rationale": "A volume-based predictive signal utilizing volume metrics, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."}]"""
    ideas = parse_llm_output(response)
    for idea in ideas:
        print(idea, '\n')