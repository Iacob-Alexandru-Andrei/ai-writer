"""Configuration loading for the ai-writer system.

Provides ``WriterSettings`` (global defaults and paths), ``load_settings``
(YAML override), and ``load_content_config`` (per-content-type config).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from writing.llm_config import LLMSettings
from writing.models import ContentConfig, ContentType

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
"""Resolved project root (two levels above ``lib/writing/``)."""

_DEFAULT_CONFIG_DIR = _PROJECT_ROOT / "config"
_DEFAULT_TEMPLATE_DIR = _PROJECT_ROOT / "templates"
_DEFAULT_CACHE_DIR = Path.home() / ".claude" / ".cache" / "writing"


class TokenBudgets(BaseModel):
    """Token budget knobs for various pipeline stages.

    Attributes:
        style_profile: Max tokens allocated to style-profile analysis.
        fewshot_per_example: Token cap per individual few-shot example.
        fewshot_total: Aggregate cap across all few-shot examples.
        running_context: Rolling context window size in tokens.
    """

    style_profile: int = 1500
    fewshot_per_example: int = 2000
    fewshot_total: int = 6000
    running_context: int = 4000


class WriterSettings(BaseModel):
    """Top-level settings for the writing system.

    Attributes:
        token_budgets: Token budget configuration.
        max_fewshot_examples: Maximum number of few-shot examples to include.
        config_dir: Directory containing content-type YAML configs.
        template_dir: Directory containing output templates.
        cache_dir: Directory for session persistence and caches.
    """

    token_budgets: TokenBudgets = Field(default_factory=TokenBudgets)
    max_fewshot_examples: int = 3
    llm: LLMSettings = Field(default_factory=LLMSettings)
    config_dir: Path = _DEFAULT_CONFIG_DIR
    template_dir: Path = _DEFAULT_TEMPLATE_DIR
    cache_dir: Path = _DEFAULT_CACHE_DIR


def load_settings(
    path: Path | None = None,
    llm_overrides: dict[str, str] | None = None,
) -> WriterSettings:
    """Load writer settings from a YAML file, falling back to defaults.

    Args:
        path: Explicit path to a ``settings.yaml`` file.  When *None* the
            function looks for ``config/settings.yaml`` relative to the
            project root.
        llm_overrides: Optional CLI-level LLM overrides.  These take
            precedence over environment variables and YAML settings.

    Returns:
        A fully populated ``WriterSettings`` instance.
    """
    if path is None:
        path = _DEFAULT_CONFIG_DIR / "settings.yaml"

    raw: dict[str, Any] = {}
    if path.exists():
        raw = yaml.safe_load(path.read_text()) or {}

    settings_data = dict(raw)
    settings_data.pop("model", None)
    settings_data["llm"] = _load_llm_settings(raw, llm_overrides)
    return WriterSettings.model_validate(settings_data)


def _load_llm_settings(
    yaml_data: dict[str, Any],
    llm_overrides: dict[str, str] | None,
) -> LLMSettings:
    """Load LLM settings with YAML, env, then CLI precedence."""
    llm_data = _normalise_llm_yaml(yaml_data)

    env_overrides = {
        "provider": os.environ.get("WRITER_PROVIDER"),
        "model": os.environ.get("WRITER_MODEL"),
        "style_model": os.environ.get("WRITER_STYLE_MODEL"),
        "outline_model": os.environ.get("WRITER_OUTLINE_MODEL"),
        "section_model": os.environ.get("WRITER_SECTION_MODEL"),
        "context_length": os.environ.get("WRITER_CONTEXT_LENGTH"),
        "max_output_tokens": os.environ.get("WRITER_MAX_OUTPUT_TOKENS"),
    }
    _apply_llm_overrides(llm_data, env_overrides)
    _apply_llm_overrides(llm_data, llm_overrides or {})
    return LLMSettings.model_validate(llm_data)


def _normalise_llm_yaml(yaml_data: dict[str, Any]) -> dict[str, Any]:
    """Return a mutable copy of the YAML LLM block."""
    raw_llm = yaml_data.get("model") or yaml_data.get("llm") or {}
    llm_data = dict(raw_llm)
    for key in ("default", "style_analysis", "outline", "section_generation"):
        value = llm_data.get(key)
        if isinstance(value, dict):
            llm_data[key] = dict(value)
    return llm_data


def _apply_llm_overrides(
    llm_data: dict[str, Any],
    overrides: dict[str, str | None],
) -> None:
    """Apply flat override values into the nested LLM settings mapping."""
    _set_model_value(llm_data, "default", "provider", overrides.get("provider"))
    _set_model_value(llm_data, "default", "model_name", overrides.get("model"))
    _set_model_value(llm_data, "style_analysis", "model_name", overrides.get("style_model"))
    _set_model_value(llm_data, "outline", "model_name", overrides.get("outline_model"))
    _set_model_value(
        llm_data,
        "section_generation",
        "model_name",
        overrides.get("section_model"),
    )
    _set_model_value(
        llm_data,
        "default",
        "context_length",
        _parse_optional_int(overrides.get("context_length")),
    )
    _set_model_value(
        llm_data,
        "default",
        "max_output_tokens",
        _parse_optional_int(overrides.get("max_output_tokens")),
    )


def _set_model_value(
    llm_data: dict[str, Any],
    stage: str,
    field_name: str,
    value: str | int | None,
) -> None:
    """Set a nested model field when an override value is present."""
    if value in (None, ""):
        return
    if not isinstance(llm_data.get(stage), dict):
        llm_data[stage] = {}
    llm_data[stage][field_name] = value


def _parse_optional_int(value: str | None) -> int | None:
    """Convert a non-empty string override to ``int``."""
    if value in (None, ""):
        return None
    return int(value)


def load_content_config(
    content_type: ContentType,
    *,
    config_dir: Path | None = None,
) -> ContentConfig:
    """Load the configuration for a specific content type.

    Reads ``config/{content_type.value}.yaml`` and returns a validated
    ``ContentConfig``.  If the file does not exist an empty config with
    sensible defaults is returned.

    Args:
        content_type: The content type to load configuration for.
        config_dir: Override for the config directory path.

    Returns:
        A ``ContentConfig`` instance for the requested type.
    """
    directory = config_dir or _DEFAULT_CONFIG_DIR
    config_path = directory / f"{content_type.value}.yaml"

    if config_path.exists():
        raw: dict[str, Any] = yaml.safe_load(config_path.read_text()) or {}
        return ContentConfig.model_validate(raw)

    return ContentConfig()
