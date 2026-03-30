"""LLM configuration models for writer settings."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

DEFAULT_CLAUDE_MODEL = "opus-4.6"
DEFAULT_CODEX_MODEL = "gpt-5.4"


class Provider(StrEnum):
    """Supported model providers."""

    CLAUDE = "claude"
    CODEX = "codex"
    AUTO = "auto"


class StageType(StrEnum):
    """Logical generation stages that may use different models."""

    STYLE_ANALYSIS = "style_analysis"
    OUTLINE = "outline"
    SECTION_GENERATION = "section_generation"
    DEFAULT = "default"


class OutlineEngine(StrEnum):
    """Available outline generation engines."""

    LLM = "llm"
    STORM = "storm"
    AUTO = "auto"


class ModelSpec(BaseModel):
    """Resolved model configuration for one stage."""

    provider: Provider = Provider.AUTO
    model_name: str | None = None
    context_length: int = 200000
    max_output_tokens: int = 16384


class LLMSettings(BaseModel):
    """Top-level LLM settings, with optional per-stage overrides."""

    default: ModelSpec = Field(default_factory=ModelSpec)
    style_analysis: ModelSpec | None = None
    outline: ModelSpec | None = None
    section_generation: ModelSpec | None = None
    outline_engine: OutlineEngine = OutlineEngine.AUTO

    def for_stage(self, stage: StageType) -> ModelSpec:
        """Return the model spec for a stage or fall back to the default."""
        if stage is StageType.DEFAULT:
            return self.default
        return getattr(self, stage.value) or self.default
