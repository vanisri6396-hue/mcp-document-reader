from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ContextStats:
    """
    Information about the current context state.
    """

    message_count: int
    estimated_tokens: int
    max_messages: int
    max_context_tokens: int
    remaining_tokens: int
    truncated_tool_results: int


class ContextManager:
    """
    Manages conversation context sent to the LLM.

    Features:
    - Message limiting
    - Safe context trimming
    - Tool-result optimization
    - Approximate token budgeting
    - Context statistics
    - Preservation of the original user request
    - Preservation of complete tool-call/result interactions
    """

    def __init__(
        self,
        max_messages: int = 20,
        max_context_tokens: int = 6000,
        max_tool_result_chars: int = 8000,
        response_token_reserve: int = 1000,
    ):
        if max_messages < 2:
            raise ValueError("max_messages must be at least 2.")

        if max_context_tokens < 100:
            raise ValueError("max_context_tokens must be at least 100.")

        if max_tool_result_chars < 100:
            raise ValueError("max_tool_result_chars must be at least 100.")

        if response_token_reserve < 0:
            raise ValueError("response_token_reserve cannot be negative.")

        if response_token_reserve >= max_context_tokens:
            raise ValueError(
                "response_token_reserve must be smaller than max_context_tokens."
            )

        self.max_messages = max_messages
        self.max_context_tokens = max_context_tokens
        self.max_tool_result_chars = max_tool_result_chars
        self.response_token_reserve = response_token_reserve

        self.messages: list[dict[str, Any]] = []

        self.truncated_tool_results = 0

    # ------------------------------------------------------------------
    # Message management
    # ------------------------------------------------------------------

    def add_message(self, message: dict[str, Any]) -> None:
        """
        Add a message to the context.

        The message must be a dictionary containing at least
        a valid role.
        """

        if not isinstance(message, dict):
            raise ValueError("Message must be a dictionary.")

        role = message.get("role")

        if not isinstance(role, str) or not role.strip():
            raise ValueError("Message must contain a valid role.")

        self.messages.append(dict(message))

    def get_messages(self) -> list[dict[str, Any]]:
        """
        Return a copy of the current context.
        """

        return [dict(message) for message in self.messages]

    def message_count(self) -> int:
        """
        Return the number of messages currently stored.
        """

        return len(self.messages)

    # ------------------------------------------------------------------
    # Tool-result optimization
    # ------------------------------------------------------------------

    def optimize_tool_result(self, content: Any) -> str:
        """
        Limit the amount of tool-result content entering the LLM context.

        Large documents can consume a large portion of the model context.
        This method safely truncates oversized results and clearly marks
        the truncation.
        """

        if content is None:
            return ""

        if not isinstance(content, str):
            content = str(content)

        if len(content) <= self.max_tool_result_chars:
            return content

        self.truncated_tool_results += 1

        visible_chars = self.max_tool_result_chars

        truncated_content = content[:visible_chars]

        return (
            "[Tool result truncated by ContextManager]\n"
            f"[Original length: {len(content)} characters]\n"
            f"[Showing first {visible_chars} characters]\n\n"
            f"{truncated_content}\n\n"
            "[End of truncated tool result]"
        )

    def add_tool_result(
        self,
        tool_name: str,
        content: Any,
        tool_call_id: str | None = None,
    ) -> None:
        """
        Add an optimized MCP tool result to the context.

        The actual result is truncated when necessary before it reaches
        the LLM.
        """

        optimized_content = self.optimize_tool_result(content)

        message: dict[str, Any] = {
            "role": "tool",
            "name": tool_name,
            "content": optimized_content,
        }

        if tool_call_id:
            message["tool_call_id"] = tool_call_id

        self.add_and_manage(message)

    # ------------------------------------------------------------------
    # Token estimation
    # ------------------------------------------------------------------

    @staticmethod
    def estimate_tokens_from_text(text: str) -> int:
        """
        Estimate token count using a simple character-based approximation.

        This intentionally does not require a tokenizer dependency.

        Approximation:
            1 token ≈ 4 characters
        """

        if not text:
            return 0

        return max(1, (len(text) + 3) // 4)

    @classmethod
    def estimate_message_tokens(cls, message: dict[str, Any]) -> int:
        """
        Estimate tokens consumed by one message.

        A small overhead is added for message metadata such as role,
        tool name, and tool-call information.
        """

        if not isinstance(message, dict):
            return 0

        token_count = 4

        for key, value in message.items():
            if value is None:
                continue

            if isinstance(value, str):
                token_count += cls.estimate_tokens_from_text(value)
            else:
                token_count += cls.estimate_tokens_from_text(str(value))

        return token_count

    def estimated_token_count(self) -> int:
        """
        Estimate total tokens currently stored in the context.
        """

        return sum(
            self.estimate_message_tokens(message)
            for message in self.messages
        )

    # ------------------------------------------------------------------
    # Context budgeting
    # ------------------------------------------------------------------

    @property
    def usable_context_tokens(self) -> int:
        """
        Maximum approximate tokens available for conversation context
        after reserving space for the LLM response.
        """

        return self.max_context_tokens - self.response_token_reserve

    def remaining_tokens(self) -> int:
        """
        Return approximate remaining context capacity.
        """

        return max(
            0,
            self.usable_context_tokens - self.estimated_token_count(),
        )

    def is_over_token_budget(self) -> bool:
        """
        Check whether the context exceeds the usable token budget.
        """

        return self.estimated_token_count() > self.usable_context_tokens

    # ------------------------------------------------------------------
    # Safe trimming
    # ------------------------------------------------------------------

    def _is_tool_interaction_start(
        self,
        message: dict[str, Any],
    ) -> bool:
        """
        Determine whether a message starts a tool interaction.

        An assistant message containing tool_calls starts an interaction.
        """

        return (
            message.get("role") == "assistant"
            and bool(message.get("tool_calls"))
        )

    def _find_complete_interactions(
        self,
    ) -> list[list[dict[str, Any]]]:
        """
        Group messages into complete conversational interactions.

        Example:

            user
            assistant + tool_call
            tool
            assistant + tool_call
            tool
            assistant final

        becomes:

            [
                [user],
                [assistant tool_call, tool],
                [assistant tool_call, tool],
                [assistant final]
            ]

        This prevents trimming an assistant tool call while leaving
        its corresponding tool result behind.
        """

        if not self.messages:
            return []

        groups: list[list[dict[str, Any]]] = []

        index = 0

        while index < len(self.messages):
            message = self.messages[index]

            if self._is_tool_interaction_start(message):
                group = [message]

                index += 1

                while index < len(self.messages):
                    next_message = self.messages[index]

                    if next_message.get("role") == "tool":
                        group.append(next_message)
                        index += 1
                        continue

                    break

                groups.append(group)
                continue

            groups.append([message])
            index += 1

        return groups

    def _trim_by_message_limit(self) -> None:
        """
        Trim old context while preserving:

        1. The original user request.
        2. Complete tool interactions.
        3. Recent conversation history.
        """

        if len(self.messages) <= self.max_messages:
            return

        if not self.messages:
            return

        original_request = self.messages[0]

        groups = self._find_complete_interactions()

        if not groups:
            return

        selected_groups: list[list[dict[str, Any]]] = []
        current_count = 1

        # Start from the newest interaction groups.
        for group in reversed(groups):
            if group == [original_request]:
                continue

            group_size = len(group)

            if current_count + group_size > self.max_messages:
                continue

            selected_groups.insert(0, group)
            current_count += group_size

        self.messages = [
            original_request,
            *[
                message
                for group in selected_groups
                for message in group
            ],
        ]

    def _trim_by_token_budget(self) -> None:
        """
        Trim oldest complete interactions until the context fits
        inside the token budget.

        The original user request is always preserved.
        """

        if not self.messages:
            return

        if not self.is_over_token_budget():
            return

        original_request = self.messages[0]

        groups = self._find_complete_interactions()

        if not groups:
            return

        remaining_groups: list[list[dict[str, Any]]] = []

        current_messages = [original_request]

        # Select newest complete groups first.
        for group in reversed(groups):
            if group == [original_request]:
                continue

            candidate_messages = [
                *current_messages,
                *group,
            ]

            candidate_tokens = sum(
                self.estimate_message_tokens(message)
                for message in candidate_messages
            )

            if candidate_tokens <= self.usable_context_tokens:
                current_messages = candidate_messages
                remaining_groups.insert(0, group)

        self.messages = current_messages

    def trim(self) -> None:
        """
        Apply both message-count and token-budget trimming.
        """

        self._trim_by_message_limit()
        self._trim_by_token_budget()

    # ------------------------------------------------------------------
    # Combined add + management
    # ------------------------------------------------------------------

    def add_and_manage(self, message: dict[str, Any]) -> None:
        """
        Add a message and immediately enforce context limits.
        """

        self.add_message(message)
        self.trim()

    def add_and_trim(self, message: dict[str, Any]) -> None:
        """
        Backwards-compatible alias for the previous ContextManager API.
        """

        self.add_and_manage(message)

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_stats(self) -> ContextStats:
        """
        Return current context statistics.
        """

        estimated_tokens = self.estimated_token_count()

        return ContextStats(
            message_count=len(self.messages),
            estimated_tokens=estimated_tokens,
            max_messages=self.max_messages,
            max_context_tokens=self.max_context_tokens,
            remaining_tokens=max(
                0,
                self.usable_context_tokens - estimated_tokens,
            ),
            truncated_tool_results=self.truncated_tool_results,
        )

    def clear(self) -> None:
        """
        Clear the complete context.
        """

        self.messages.clear()
        self.truncated_tool_results = 0