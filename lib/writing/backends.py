"""Abstract LLM dispatch interface for the ai-writer system.

Provides a backend abstraction so the writing pipeline can call language
models through either the ``claude -p`` CLI (standalone execution) or the
Agent tool (when running inside a Claude Code session).  No direct
``anthropic.Anthropic()`` client usage -- all calls route through Claude
Code's built-in model access (R14).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import warnings
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar
from uuid import uuid4

from pydantic import TypeAdapter
from writing.llm_config import (
    DEFAULT_CLAUDE_MODEL,
    DEFAULT_CODEX_MODEL,
    LLMSettings,
    ModelSpec,
    Provider,
    StageType,
)

_T = TypeVar("_T")
logger = logging.getLogger(__name__)


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

    def __init__(
        self,
        model_name: str | None = None,
        context_length: int = 200000,
        max_output_tokens: int = 16384,
    ) -> None:
        self.model_name = model_name
        self.context_length = context_length
        self.max_output_tokens = max_output_tokens

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
        if self.model_name:
            cmd.extend(["--model", self.model_name])
        # Note: claude -p does not support --max-tokens; token budget is
        # enforced at the prompt-assembly level via self.max_output_tokens.
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


class CodexBackend(LLMBackend):
    """Backend that shells out to ``codex-run`` for generation."""

    CODEX_BIN = Path.home() / ".claude" / "bin" / "codex-run"

    def __init__(
        self,
        model_name: str | None = None,
        context_length: int = 200000,
        max_output_tokens: int = 16384,
    ) -> None:
        self.model_name = model_name
        self.context_length = context_length
        self.max_output_tokens = max_output_tokens

    def generate(self, prompt: str, system: str | None = None) -> str:
        """Run ``codex-run`` and return the generated file content."""
        output_file = Path("/tmp") / f"codex-gen-{uuid4().hex[:8]}.md"
        combined_prompt = f"{system}\n\n{prompt}" if system else prompt

        cmd = [
            str(self.CODEX_BIN),
            str(output_file),
            "exec",
            "--full-auto",
            "--skip-git-repo-check",
            "--color",
            "never",
        ]
        if self.model_name:
            cmd.extend(["-m", self.model_name])
        cmd.append(combined_prompt)

        try:
            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=7200,
            )
        except subprocess.TimeoutExpired as exc:
            msg = f"codex-run timed out after 7200 seconds: {exc}"
            raise RuntimeError(msg) from exc
        except OSError as exc:
            msg = f"codex-run failed to start: {exc}"
            raise RuntimeError(msg) from exc

        try:
            if result.returncode != 0:
                stderr = result.stderr.strip()
                stdout = result.stdout.strip()
                details = stderr or stdout or "no subprocess output"
                msg = f"codex-run failed (rc={result.returncode}): {details}"
                raise RuntimeError(msg)
            return output_file.read_text(encoding="utf-8").strip()
        except OSError as exc:
            msg = f"codex-run did not produce a readable output file: {exc}"
            raise RuntimeError(msg) from exc
        finally:
            output_file.unlink(missing_ok=True)

    def generate_structured(self, prompt: str, schema: type[_T]) -> _T:
        """Generate JSON via ``codex-run`` and parse into *schema*."""
        adapter: TypeAdapter[_T] = TypeAdapter(schema)
        json_schema = json.dumps(adapter.json_schema(), indent=2)

        augmented_prompt = (
            f"{prompt}\n\n"
            f"Respond ONLY with valid JSON matching this schema:\n"
            f"```json\n{json_schema}\n```"
        )
        raw = self.generate(augmented_prompt)
        cleaned = _strip_json_fences(raw)
        return adapter.validate_json(cleaned)


class FallbackBackend(LLMBackend):
    """Backend wrapper that retries with a secondary backend on runtime failures."""

    def __init__(self, primary: LLMBackend, secondary: LLMBackend) -> None:
        self.primary = primary
        self.secondary = secondary

    def generate(self, prompt: str, system: str | None = None) -> str:
        """Run generation with fallback on transport/runtime failures."""
        try:
            return self.primary.generate(prompt, system)
        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            RuntimeError,
            OSError,
            FileNotFoundError,
        ) as exc:
            logger.warning(
                "Primary backend %s failed; falling back to %s: %s",
                type(self.primary).__name__,
                type(self.secondary).__name__,
                exc,
            )
            return self.secondary.generate(prompt, system)

    def generate_structured(self, prompt: str, schema: type[_T]) -> _T:
        """Run structured generation with fallback on transport/runtime failures."""
        try:
            return self.primary.generate_structured(prompt, schema)
        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            RuntimeError,
            OSError,
            FileNotFoundError,
        ) as exc:
            logger.warning(
                "Primary backend %s failed; falling back to %s: %s",
                type(self.primary).__name__,
                type(self.secondary).__name__,
                exc,
            )
            return self.secondary.generate_structured(prompt, schema)


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
    warnings.warn(
        "get_backend() is deprecated; use resolve_backend() for stage-aware routing.",
        DeprecationWarning,
        stacklevel=2,
    )
    if os.environ.get("CLAUDE_CODE_SESSION"):
        return AgentBackend()
    return ClaudeCLIBackend()


def read_routing_state() -> str:
    """Read the current routing state and return the primary provider."""
    try:
        payload = json.loads(Path("/tmp/orch-routing.json").read_text(encoding="utf-8"))
        primary = payload["primary"]
        if not isinstance(primary, str):
            raise TypeError("primary must be a string")
        return primary
    except (OSError, ValueError, TypeError, KeyError):
        return Provider.CLAUDE.value


def resolve_backend(stage: StageType, settings: LLMSettings) -> LLMBackend:
    """Resolve a stage-specific backend with fallback to the alternate provider."""
    spec = settings.for_stage(stage)
    provider_name = spec.provider.value
    if provider_name == Provider.AUTO.value:
        provider_name = read_routing_state()

    primary = _build_backend_for_provider(provider_name, spec)
    secondary_provider = (
        Provider.CLAUDE.value if provider_name == Provider.CODEX.value else Provider.CODEX.value
    )
    secondary = _build_backend_for_provider(secondary_provider, spec)
    return FallbackBackend(primary, secondary)


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


def _build_backend_for_provider(provider_name: str, spec: ModelSpec) -> LLMBackend:
    """Instantiate the requested backend type for a resolved provider."""
    if provider_name == Provider.CODEX.value:
        return CodexBackend(
            model_name=spec.model_name or DEFAULT_CODEX_MODEL,
            context_length=spec.context_length,
            max_output_tokens=spec.max_output_tokens,
        )
    return ClaudeCLIBackend(
        model_name=spec.model_name or DEFAULT_CLAUDE_MODEL,
        context_length=spec.context_length,
        max_output_tokens=spec.max_output_tokens,
    )
