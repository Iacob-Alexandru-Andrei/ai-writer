"""Tests for writing.backends configuration and routing behavior."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from writing.backends import (
    ClaudeCLIBackend,
    CodexBackend,
    FallbackBackend,
    read_routing_state,
    resolve_backend,
)
from writing.llm_config import (
    DEFAULT_CLAUDE_MODEL,
    DEFAULT_CODEX_MODEL,
    LLMSettings,
    ModelSpec,
    Provider,
    StageType,
)


def test_claude_cli_backend_default_command_has_no_model_flag() -> None:
    backend = ClaudeCLIBackend()

    completed = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=" generated text \n",
        stderr="",
    )
    with patch("writing.backends.subprocess.run", return_value=completed) as mock_run:
        result = backend.generate("Write an introduction.")

    cmd = mock_run.call_args.args[0]
    assert result == "generated text"
    assert cmd[:2] == ["claude", "-p"]
    assert "--model" not in cmd
    # claude -p does not support --max-tokens; budget enforced at prompt assembly
    assert "--max-tokens" not in cmd
    assert cmd[-1] == "Write an introduction."


def test_claude_cli_backend_includes_model_flag_when_model_name_is_set() -> None:
    backend = ClaudeCLIBackend(model_name="haiku")

    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")
    with patch("writing.backends.subprocess.run", return_value=completed) as mock_run:
        backend.generate("Prompt")

    cmd = mock_run.call_args.args[0]
    assert cmd[cmd.index("--model") + 1] == "haiku"


def test_claude_cli_backend_stores_max_output_tokens() -> None:
    backend = ClaudeCLIBackend(max_output_tokens=2048)
    # max_output_tokens is stored for prompt budget calculation but not passed to CLI
    assert backend.max_output_tokens == 2048

    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")
    with patch("writing.backends.subprocess.run", return_value=completed) as mock_run:
        backend.generate("Prompt")

    cmd = mock_run.call_args.args[0]
    assert "--max-tokens" not in cmd


def test_codex_backend_command_includes_output_file_full_auto_and_prompt() -> None:
    backend = CodexBackend()

    def fake_run(cmd: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        Path(cmd[1]).write_text("codex output", encoding="utf-8")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    with patch("writing.backends.subprocess.run", side_effect=fake_run) as mock_run:
        result = backend.generate("Draft the section.")

    cmd = mock_run.call_args.args[0]
    assert result == "codex output"
    assert cmd[0] == str(CodexBackend.CODEX_BIN)
    assert Path(cmd[1]).parent == Path("/tmp")
    assert cmd[2] == "exec"
    assert "--full-auto" in cmd
    assert cmd[-1] == "Draft the section."
    assert not Path(cmd[1]).exists()


def test_codex_backend_includes_model_flag_when_model_name_is_set() -> None:
    backend = CodexBackend(model_name="gpt-5.4-mini")

    def fake_run(cmd: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        Path(cmd[1]).write_text("codex output", encoding="utf-8")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    with patch("writing.backends.subprocess.run", side_effect=fake_run) as mock_run:
        backend.generate("Prompt")

    cmd = mock_run.call_args.args[0]
    assert cmd[cmd.index("-m") + 1] == "gpt-5.4-mini"


def test_codex_backend_prepends_system_prompt_to_prompt_body() -> None:
    backend = CodexBackend()

    def fake_run(cmd: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        Path(cmd[1]).write_text("codex output", encoding="utf-8")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    with patch("writing.backends.subprocess.run", side_effect=fake_run) as mock_run:
        backend.generate("User prompt", system="System prompt")

    cmd = mock_run.call_args.args[0]
    assert cmd[-1] == "System prompt\n\nUser prompt"


def test_fallback_backend_returns_primary_result_without_using_secondary() -> None:
    primary = MagicMock()
    secondary = MagicMock()
    primary.generate.return_value = "primary result"
    backend = FallbackBackend(primary, secondary)

    result = backend.generate("Prompt")

    assert result == "primary result"
    primary.generate.assert_called_once_with("Prompt", None)
    secondary.generate.assert_not_called()


def test_fallback_backend_uses_secondary_when_primary_raises_runtime_error() -> None:
    primary = MagicMock()
    secondary = MagicMock()
    primary.generate.side_effect = RuntimeError("primary failed")
    secondary.generate.return_value = "secondary result"
    backend = FallbackBackend(primary, secondary)

    result = backend.generate("Prompt")

    assert result == "secondary result"
    secondary.generate.assert_called_once_with("Prompt", None)


def test_fallback_backend_uses_secondary_when_primary_times_out() -> None:
    primary = MagicMock()
    secondary = MagicMock()
    primary.generate.side_effect = subprocess.TimeoutExpired(cmd="codex-run", timeout=5)
    secondary.generate.return_value = "secondary result"
    backend = FallbackBackend(primary, secondary)

    result = backend.generate("Prompt")

    assert result == "secondary result"
    secondary.generate.assert_called_once_with("Prompt", None)


def test_fallback_backend_raises_secondary_exception_when_both_fail() -> None:
    primary = MagicMock()
    secondary = MagicMock()
    primary.generate.side_effect = RuntimeError("primary failed")
    secondary.generate.side_effect = ValueError("secondary failed")
    backend = FallbackBackend(primary, secondary)

    with pytest.raises(ValueError, match="secondary failed"):
        backend.generate("Prompt")


def test_read_routing_state_returns_primary_from_valid_json() -> None:
    with patch(
        "writing.backends.Path.read_text",
        return_value='{"primary": "codex"}',
    ):
        assert read_routing_state() == "codex"


def test_read_routing_state_returns_claude_when_file_is_missing() -> None:
    with patch("writing.backends.Path.read_text", side_effect=FileNotFoundError):
        assert read_routing_state() == "claude"


def test_read_routing_state_returns_claude_when_json_is_malformed() -> None:
    with patch("writing.backends.Path.read_text", return_value="{not-json"):
        assert read_routing_state() == "claude"


def test_resolve_backend_with_explicit_claude_provider_uses_claude_primary() -> None:
    settings = LLMSettings(outline=ModelSpec(provider=Provider.CLAUDE))

    backend = resolve_backend(StageType.OUTLINE, settings)

    assert isinstance(backend, FallbackBackend)
    assert isinstance(backend.primary, ClaudeCLIBackend)
    assert isinstance(backend.secondary, CodexBackend)
    assert backend.primary.model_name == DEFAULT_CLAUDE_MODEL


def test_resolve_backend_with_explicit_codex_provider_uses_codex_primary() -> None:
    settings = LLMSettings(default=ModelSpec(provider=Provider.CODEX))

    backend = resolve_backend(StageType.DEFAULT, settings)

    assert isinstance(backend, FallbackBackend)
    assert isinstance(backend.primary, CodexBackend)
    assert isinstance(backend.secondary, ClaudeCLIBackend)
    assert backend.primary.model_name == DEFAULT_CODEX_MODEL


def test_resolve_backend_with_auto_provider_uses_routing_state_primary() -> None:
    settings = LLMSettings(default=ModelSpec(provider=Provider.AUTO))

    with patch("writing.backends.read_routing_state", return_value="codex"):
        backend = resolve_backend(StageType.SECTION_GENERATION, settings)

    assert isinstance(backend, FallbackBackend)
    assert isinstance(backend.primary, CodexBackend)
    assert isinstance(backend.secondary, ClaudeCLIBackend)
    assert backend.primary.model_name == DEFAULT_CODEX_MODEL
