"""Abstract LLM dispatch interface for the ai-writer system.

Provides a backend abstraction so the writing pipeline can call language
models through either the ``claude -p`` CLI (standalone execution) or the
Agent tool (when running inside a Claude Code session).  No direct
``anthropic.Anthropic()`` client usage -- all calls route through Claude
Code's built-in model access (R14).
"""

from __future__ import annotations

import json
import os
import subprocess
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import TypeAdapter

_T = TypeVar("_T")


class LLMBackend(ABC):
    """Abstract base class for language-model backends.

    Subclasses must implement ``generate`` (free-form text completion) and
    ``generate_structured`` (JSON-schema-constrained output parsed into a
    Pydantic model or dataclass).
    """

    @abstractmethod
    def generate(self, prompt: str, system: str | None = None) -> str:
        """Generate a free-form text response.

        Args:
            prompt: The user/instruction prompt.
            system: Optional system prompt prepended to the conversation.

        Returns:
            The model's text response.
        """

    @abstractmethod
    def generate_structured(self, prompt: str, schema: type[_T]) -> _T:
        """Generate a response conforming to a Pydantic model schema.

        The backend serialises the model's JSON schema, instructs the LLM
        to return valid JSON, and parses the result.

        Args:
            prompt: The user/instruction prompt.
            schema: A Pydantic ``BaseModel`` subclass or other type
                supported by ``pydantic.TypeAdapter``.

        Returns:
            An instance of *schema* populated from the model's response.
        """


class ClaudeCLIBackend(LLMBackend):
    """Backend that shells out to ``claude -p`` for generation.

    Suitable for standalone scripts and CI environments where Claude Code
    is installed but the calling process is not a Claude Code session.
    """

    def generate(self, prompt: str, system: str | None = None) -> str:
        """Run ``claude -p`` and return stdout.

        Args:
            prompt: The user prompt forwarded to ``claude -p``.
            system: Optional system prompt passed via ``--system-prompt``.

        Returns:
            Stripped stdout from the CLI invocation.

        Raises:
            RuntimeError: If the subprocess exits with a non-zero code.
        """
        cmd: list[str] = ["claude", "-p"]
        if system:
            cmd.extend(["--system-prompt", system])
        cmd.append(prompt)

        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            msg = f"claude -p failed (rc={result.returncode}): {result.stderr.strip()}"
            raise RuntimeError(msg)
        return result.stdout.strip()

    def generate_structured(self, prompt: str, schema: type[_T]) -> _T:
        """Generate JSON via ``claude -p`` and parse into *schema*.

        Args:
            prompt: The user prompt.
            schema: Target Pydantic type.

        Returns:
            Parsed instance of *schema*.
        """
        adapter: TypeAdapter[_T] = TypeAdapter(schema)
        json_schema = json.dumps(adapter.json_schema(), indent=2)

        augmented_prompt = (
            f"{prompt}\n\n"
            f"Respond ONLY with valid JSON matching this schema:\n"
            f"```json\n{json_schema}\n```"
        )
        raw = self.generate(augmented_prompt)

        # Strip markdown fences if the model wraps the output.
        cleaned = _strip_json_fences(raw)
        return adapter.validate_json(cleaned)


class AgentBackend(LLMBackend):
    """Placeholder backend for Agent-tool dispatch inside Claude Code.

    When the writing pipeline runs as a sub-agent within Claude Code, LLM
    calls should route through the Agent tool rather than spawning a CLI
    subprocess.  This class provides the interface; actual dispatch logic
    will be wired once the orchestration layer is in place.
    """

    def generate(self, prompt: str, system: str | None = None) -> str:
        """Dispatch via the Agent tool (not yet implemented).

        Args:
            prompt: The user prompt.
            system: Optional system prompt.

        Returns:
            The agent's text response.

        Raises:
            NotImplementedError: Always, until agent dispatch is wired.
        """
        msg = (
            "AgentBackend.generate is a placeholder. "
            "Wire Agent tool dispatch in the orchestration layer."
        )
        raise NotImplementedError(msg)

    def generate_structured(self, prompt: str, schema: type[_T]) -> _T:
        """Dispatch structured generation via the Agent tool (not yet implemented).

        Args:
            prompt: The user prompt.
            schema: Target Pydantic type.

        Returns:
            Parsed instance of *schema*.

        Raises:
            NotImplementedError: Always, until agent dispatch is wired.
        """
        msg = (
            "AgentBackend.generate_structured is a placeholder. "
            "Wire Agent tool dispatch in the orchestration layer."
        )
        raise NotImplementedError(msg)


def get_backend() -> LLMBackend:
    """Select the appropriate LLM backend based on the runtime environment.

    Returns ``AgentBackend`` when the ``CLAUDE_CODE_SESSION`` environment
    variable is set (indicating execution inside a Claude Code agent tree),
    otherwise falls back to ``ClaudeCLIBackend``.

    Returns:
        An ``LLMBackend`` instance ready for use.
    """
    if os.environ.get("CLAUDE_CODE_SESSION"):
        return AgentBackend()
    return ClaudeCLIBackend()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_json_fences(text: str) -> str:
    """Remove optional markdown JSON fences from model output.

    Args:
        text: Raw model output that may be wrapped in triple-backtick
            fences with an optional ``json`` language tag.

    Returns:
        The inner JSON string with surrounding whitespace stripped.
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        # Remove opening fence (with optional language tag).
        first_newline = stripped.index("\n")
        stripped = stripped[first_newline + 1 :]
        # Remove closing fence.
        stripped = stripped.removesuffix("```")
    return stripped.strip()
