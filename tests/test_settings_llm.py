"""Tests for writing.settings LLM loading and precedence rules."""

from __future__ import annotations

from pathlib import Path

from writing.llm_config import OutlineEngine, Provider
from writing.settings import load_settings

LLM_ENV_VARS = (
    "WRITER_PROVIDER",
    "WRITER_MODEL",
    "WRITER_STYLE_MODEL",
    "WRITER_OUTLINE_MODEL",
    "WRITER_SECTION_MODEL",
    "WRITER_CONTEXT_LENGTH",
    "WRITER_MAX_OUTPUT_TOKENS",
)


def _clear_llm_env(monkeypatch) -> None:
    for name in LLM_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def _write_settings(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_load_settings_with_no_args_returns_defaults(tmp_path, monkeypatch) -> None:
    import writing.settings as settings_module

    _clear_llm_env(monkeypatch)
    monkeypatch.setattr(settings_module, "_DEFAULT_CONFIG_DIR", tmp_path / "config")

    settings = load_settings()

    assert settings.llm.default.provider is Provider.AUTO
    assert settings.llm.default.model_name is None
    assert settings.llm.outline_engine is OutlineEngine.AUTO


def test_load_settings_reads_yaml_model_section(tmp_path, monkeypatch) -> None:
    _clear_llm_env(monkeypatch)
    path = _write_settings(
        tmp_path / "settings.yaml",
        """
model:
  default:
    provider: codex
    model_name: yaml-default
    context_length: 123456
    max_output_tokens: 2048
  style_analysis:
    model_name: yaml-style
  outline_engine: storm
""".strip()
        + "\n",
    )

    settings = load_settings(path)

    assert settings.llm.default.provider is Provider.CODEX
    assert settings.llm.default.model_name == "yaml-default"
    assert settings.llm.default.context_length == 123456
    assert settings.llm.default.max_output_tokens == 2048
    assert settings.llm.style_analysis is not None
    assert settings.llm.style_analysis.model_name == "yaml-style"
    assert settings.llm.outline_engine is OutlineEngine.STORM


def test_writer_provider_env_var_overrides_yaml(tmp_path, monkeypatch) -> None:
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("WRITER_PROVIDER", "claude")
    path = _write_settings(
        tmp_path / "settings.yaml",
        """
model:
  default:
    provider: codex
""".strip()
        + "\n",
    )

    settings = load_settings(path)

    assert settings.llm.default.provider is Provider.CLAUDE


def test_writer_model_env_var_overrides_yaml_default_model_name(
    tmp_path,
    monkeypatch,
) -> None:
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("WRITER_MODEL", "env-model")
    path = _write_settings(
        tmp_path / "settings.yaml",
        """
model:
  default:
    model_name: yaml-model
""".strip()
        + "\n",
    )

    settings = load_settings(path)

    assert settings.llm.default.model_name == "env-model"


def test_cli_llm_overrides_take_precedence_over_env_vars(tmp_path, monkeypatch) -> None:
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("WRITER_PROVIDER", "claude")
    monkeypatch.setenv("WRITER_MODEL", "env-model")
    path = _write_settings(
        tmp_path / "settings.yaml",
        """
model:
  default:
    provider: auto
    model_name: yaml-model
""".strip()
        + "\n",
    )

    settings = load_settings(
        path,
        llm_overrides={"provider": "codex", "model": "cli-model"},
    )

    assert settings.llm.default.provider is Provider.CODEX
    assert settings.llm.default.model_name == "cli-model"


def test_load_settings_uses_yaml_then_env_then_cli_precedence(
    tmp_path,
    monkeypatch,
) -> None:
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("WRITER_PROVIDER", "claude")
    path = _write_settings(
        tmp_path / "settings.yaml",
        """
model:
  default:
    provider: auto
""".strip()
        + "\n",
    )

    settings = load_settings(path, llm_overrides={"provider": "codex"})

    assert settings.llm.default.provider is Provider.CODEX


def test_stage_specific_env_vars_override_stage_model_names(tmp_path, monkeypatch) -> None:
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("WRITER_STYLE_MODEL", "style-env")
    monkeypatch.setenv("WRITER_SECTION_MODEL", "section-env")
    path = _write_settings(tmp_path / "settings.yaml", "{}\n")

    settings = load_settings(path)

    assert settings.llm.style_analysis is not None
    assert settings.llm.style_analysis.model_name == "style-env"
    assert settings.llm.section_generation is not None
    assert settings.llm.section_generation.model_name == "section-env"
