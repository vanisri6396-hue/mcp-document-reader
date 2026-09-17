"""
AI-specific safety controls for the MCP document agent.

This module sits between the LLM and MCP tool execution.

It provides:
- Tool allowlisting
- Tool-name validation
- Argument validation
- Prompt-injection detection
- Dangerous-path detection
- Risk classification
- Destructive-tool confirmation
- Safe tool-call enforcement

This layer does NOT replace:
- Authentication
- Authorization
- Input validation
- Rate limiting
- MCP server security
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Tool policy
# ---------------------------------------------------------------------------

ALLOWED_TOOLS = {
    "read_document",
    "list_documents",
    "search_documents",
    "create_document",
    "update_document",
    "delete_document",
    "document_resource",
    "summarize_document",
}

DESTRUCTIVE_TOOLS = {
    "delete_document",
}

WRITE_TOOLS = {
    "create_document",
    "update_document",
    "delete_document",
}


# ---------------------------------------------------------------------------
# Prompt-injection patterns
# ---------------------------------------------------------------------------

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?prior\s+instructions",
    r"disregard\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(all\s+)?prior\s+instructions",
    r"forget\s+(all\s+)?previous\s+instructions",
    r"forget\s+(all\s+)?prior\s+instructions",
    r"override\s+(the\s+)?system\s+instructions",
    r"override\s+(all\s+)?instructions",
    r"reveal\s+(the\s+)?system\s+prompt",
    r"show\s+(the\s+)?system\s+prompt",
    r"print\s+(the\s+)?system\s+prompt",
    r"reveal\s+(your\s+)?hidden\s+instructions",
    r"developer\s+message",
    r"system\s+message",
    r"jailbreak",
]


# ---------------------------------------------------------------------------
# Dangerous path patterns
# ---------------------------------------------------------------------------

DANGEROUS_PATH_PATTERNS = [
    r"\.\.",
    r"^[\\/]",
    r"^[a-zA-Z]:[\\/]",
]


# ---------------------------------------------------------------------------
# Safety result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    reason: str
    risk_level: str
    tool_name: str
    requires_confirmation: bool = False


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class AISafetyError(Exception):
    """Base exception for AI safety failures."""


class UnsafeToolCallError(AISafetyError):
    """Raised when an LLM-generated tool call is unsafe."""


class ConfirmationRequiredError(AISafetyError):
    """Raised when a destructive operation requires confirmation."""


# ---------------------------------------------------------------------------
# Tool name validation
# ---------------------------------------------------------------------------

def validate_tool_name(tool_name: str) -> str:
    if not isinstance(tool_name, str):
        raise UnsafeToolCallError(
            "Tool name must be a string."
        )

    tool_name = tool_name.strip()

    if not tool_name:
        raise UnsafeToolCallError(
            "Tool name cannot be empty."
        )

    if len(tool_name) > 100:
        raise UnsafeToolCallError(
            "Tool name is too long."
        )

    if not re.fullmatch(
        r"[a-zA-Z0-9_-]+",
        tool_name,
    ):
        raise UnsafeToolCallError(
            "Tool name contains invalid characters."
        )

    return tool_name


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------

def validate_arguments(arguments: Any) -> dict[str, Any]:
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError as error:
            raise UnsafeToolCallError(
                f"Tool arguments are not valid JSON: {error}"
            ) from error

    elif isinstance(arguments, dict):
        parsed = arguments

    else:
        raise UnsafeToolCallError(
            "Tool arguments must be a JSON object."
        )

    if not isinstance(parsed, dict):
        raise UnsafeToolCallError(
            "Tool arguments must decode to a JSON object."
        )

    return parsed


# ---------------------------------------------------------------------------
# Prompt-injection detection
# ---------------------------------------------------------------------------

def detect_prompt_injection(value: Any) -> list[str]:
    findings: list[str] = []

    if isinstance(value, dict):
        for key, item in value.items():
            findings.extend(
                detect_prompt_injection(key)
            )
            findings.extend(
                detect_prompt_injection(item)
            )

        return findings

    if isinstance(value, list):
        for item in value:
            findings.extend(
                detect_prompt_injection(item)
            )

        return findings

    if not isinstance(value, str):
        return findings

    normalized = value.lower()

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, normalized):
            findings.append(
                f"Prompt-injection pattern detected: {pattern}"
            )

    return findings


# ---------------------------------------------------------------------------
# Dangerous path detection
# ---------------------------------------------------------------------------

def detect_dangerous_paths(value: Any) -> list[str]:
    findings: list[str] = []

    if isinstance(value, dict):
        for item in value.values():
            findings.extend(
                detect_dangerous_paths(item)
            )

        return findings

    if isinstance(value, list):
        for item in value:
            findings.extend(
                detect_dangerous_paths(item)
            )

        return findings

    if not isinstance(value, str):
        return findings

    for pattern in DANGEROUS_PATH_PATTERNS:
        if re.search(pattern, value):
            findings.append(
                "Potentially dangerous path pattern detected."
            )
            break

    return findings


# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------

def classify_tool_risk(tool_name: str) -> str:
    if tool_name in DESTRUCTIVE_TOOLS:
        return "high"

    if tool_name in WRITE_TOOLS:
        return "medium"

    if tool_name in {
        "read_document",
        "list_documents",
        "search_documents",
        "document_resource",
        "summarize_document",
    }:
        return "low"

    return "unknown"


# ---------------------------------------------------------------------------
# Confirmation policy
# ---------------------------------------------------------------------------

def requires_confirmation(tool_name: str) -> bool:
    return tool_name in DESTRUCTIVE_TOOLS


def validate_confirmation(
    tool_name: str,
    confirmed: bool,
) -> None:

    if not requires_confirmation(tool_name):
        return

    if confirmed is not True:
        raise ConfirmationRequiredError(
            f"Explicit confirmation is required before executing "
            f"destructive tool '{tool_name}'."
        )


# ---------------------------------------------------------------------------
# Main inspection
# ---------------------------------------------------------------------------

def inspect_tool_call(
    tool_name: str,
    arguments: Any,
) -> SafetyDecision:

    try:
        normalized_tool_name = validate_tool_name(
            tool_name
        )

    except UnsafeToolCallError as error:
        return SafetyDecision(
            allowed=False,
            reason=str(error),
            risk_level="high",
            tool_name=str(tool_name),
            requires_confirmation=False,
        )

    # Tool allowlist
    if normalized_tool_name not in ALLOWED_TOOLS:
        return SafetyDecision(
            allowed=False,
            reason=(
                f"Tool '{normalized_tool_name}' is not "
                "allowed by the AI safety policy."
            ),
            risk_level="high",
            tool_name=normalized_tool_name,
            requires_confirmation=False,
        )

    # Argument validation
    try:
        parsed_arguments = validate_arguments(
            arguments
        )

    except UnsafeToolCallError as error:
        return SafetyDecision(
            allowed=False,
            reason=str(error),
            risk_level="high",
            tool_name=normalized_tool_name,
            requires_confirmation=False,
        )

    # Prompt injection
    injection_findings = detect_prompt_injection(
        parsed_arguments
    )

    if injection_findings:
        return SafetyDecision(
            allowed=False,
            reason=(
                "Suspicious instruction-like content detected "
                "inside tool arguments."
            ),
            risk_level="high",
            tool_name=normalized_tool_name,
            requires_confirmation=False,
        )

    # Dangerous paths
    path_findings = detect_dangerous_paths(
        parsed_arguments
    )

    if path_findings:
        return SafetyDecision(
            allowed=False,
            reason=(
                "Potentially dangerous path content detected "
                "inside tool arguments."
            ),
            risk_level="high",
            tool_name=normalized_tool_name,
            requires_confirmation=False,
        )

    risk_level = classify_tool_risk(
        normalized_tool_name
    )

    return SafetyDecision(
        allowed=True,
        reason="Tool call passed AI safety inspection.",
        risk_level=risk_level,
        tool_name=normalized_tool_name,
        requires_confirmation=requires_confirmation(
            normalized_tool_name
        ),
    )


# ---------------------------------------------------------------------------
# Enforcement
# ---------------------------------------------------------------------------

def enforce_tool_safety(
    tool_name: str,
    arguments: Any,
    confirmed: bool = False,
) -> dict[str, Any]:

    decision = inspect_tool_call(
        tool_name,
        arguments,
    )

    if not decision.allowed:
        raise UnsafeToolCallError(
            decision.reason
        )

    validate_confirmation(
        decision.tool_name,
        confirmed,
    )

    return validate_arguments(
        arguments
    )