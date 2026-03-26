"""Configuration loading for the ai-writer system.

Provides ``WriterSettings`` (global defaults and paths), ``load_settings``
(YAML override), and ``load_content_config`` (per-content-type config).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

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
    config_dir: Path = _DEFAULT_CONFIG_DIR
    template_dir: Path = _DEFAULT_TEMPLATE_DIR
    cache_dir: Path = _DEFAULT_CACHE_DIR


def load_settings(path: Path | None = None) -> WriterSettings:
    """Load writer settings from a YAML file, falling back to defaults.

    Args:
        path: Explicit path to a ``settings.yaml`` file.  When *None* the
            function looks for ``config/settings.yaml`` relative to the
            project root.

    Returns:
        A fully populated ``WriterSettings`` instance.
    """
    if path is None:
        path = _DEFAULT_CONFIG_DIR / "settings.yaml"

    if path.exists():
        raw: dict[str, Any] = yaml.safe_load(path.read_text()) or {}
        return WriterSettings.model_validate(raw)

    return WriterSettings()


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
