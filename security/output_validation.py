"""
Validation for final LLM responses.

This layer provides lightweight output safety checks.

It does not attempt to mathematically prove that every statement
is factually correct. Instead, it ensures that the agent:

- Produces a usable answer.
- Does not return empty output.
- Does not expose internal tool-call structures.
- Does not follow obvious instruction-injection patterns.
- Does not expose internal system/developer instructions.
- Stays within a reasonable response size.

Grounding is additionally encouraged through the agent's system prompt.
"""

from __future__ import annotations

import re


MAX_FINAL_ANSWER_CHARS = 12_000


UNSAFE_OUTPUT_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?prior\s+instructions",
    r"reveal\s+(the\s+)?system\s+prompt",
    r"show\s+(the\s+)?system\s+prompt",
    r"developer\s+message",
    r"hidden\s+instructions",
]


class UnsafeOutputError(Exception):
    """Raised when an LLM final response fails safety validation."""


def validate_final_answer(answer: str) -> str:
    if not isinstance(answer, str):
        raise UnsafeOutputError(
            "Final answer must be text."
        )

    answer = answer.strip()

    if not answer:
        raise UnsafeOutputError(
            "LLM returned an empty final answer."
        )

    if len(answer) > MAX_FINAL_ANSWER_CHARS:
        raise UnsafeOutputError(
            "LLM final answer exceeds the maximum allowed length."
        )

    normalized = answer.lower()

    for pattern in UNSAFE_OUTPUT_PATTERNS:
        if re.search(pattern, normalized):
            raise UnsafeOutputError(
                "Final answer contains unsafe instruction-like content."
            )

    # Prevent accidental exposure of raw internal tool-call structures.
    if '"tool_calls"' in normalized:
        raise UnsafeOutputError(
            "Final answer appears to contain internal tool-call data."
        )

    if '"function"' in normalized and '"arguments"' in normalized:
        raise UnsafeOutputError(
            "Final answer appears to contain internal tool-call data."
        )

    return answer