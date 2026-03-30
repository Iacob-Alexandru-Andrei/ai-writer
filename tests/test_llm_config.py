"""Tests for writing.llm_config types and stage resolution."""

from __future__ import annotations

from writing.llm_config import LLMSettings, ModelSpec, OutlineEngine, Provider, StageType


def test_provider_enum_values() -> None:
    assert Provider.CLAUDE.value == "claude"
    assert Provider.CODEX.value == "codex"
    assert Provider.AUTO.value == "auto"


def test_stage_type_enum_values() -> None:
    assert StageType.STYLE_ANALYSIS.value == "style_analysis"
    assert StageType.OUTLINE.value == "outline"
    assert StageType.SECTION_GENERATION.value == "section_generation"
    assert StageType.DEFAULT.value == "default"


def test_outline_engine_enum_values() -> None:
    assert OutlineEngine.LLM.value == "llm"
    assert OutlineEngine.STORM.value == "storm"
    assert OutlineEngine.AUTO.value == "auto"


def test_model_spec_defaults() -> None:
    spec = ModelSpec()

    assert spec.provider is Provider.AUTO
    assert spec.model_name is None
    assert spec.context_length == 200000
    assert spec.max_output_tokens == 16384


def test_model_spec_custom_values() -> None:
    spec = ModelSpec(
        provider=Provider.CODEX,
        model_name="gpt-5.4",
        context_length=131072,
        max_output_tokens=4096,
    )

    assert spec.provider is Provider.CODEX
    assert spec.model_name == "gpt-5.4"
    assert spec.context_length == 131072
    assert spec.max_output_tokens == 4096


def test_llm_settings_defaults() -> None:
    settings = LLMSettings()

    assert settings.default == ModelSpec()
    assert settings.style_analysis is None
    assert settings.outline is None
    assert settings.section_generation is None
    assert settings.outline_engine is OutlineEngine.AUTO


def test_llm_settings_for_stage_returns_stage_specific_model() -> None:
    override = ModelSpec(provider=Provider.CLAUDE, model_name="haiku")
    settings = LLMSettings(style_analysis=override)

    assert settings.for_stage(StageType.STYLE_ANALYSIS) is override


def test_llm_settings_for_stage_falls_back_to_default_when_override_missing() -> None:
    default = ModelSpec(provider=Provider.CODEX, model_name="gpt-5.4")
    settings = LLMSettings(default=default)

    assert settings.for_stage(StageType.OUTLINE) is default


def test_llm_settings_for_stage_default_always_returns_default() -> None:
    default = ModelSpec(provider=Provider.CLAUDE, model_name="opus-4.6")
    settings = LLMSettings(
        default=default,
        section_generation=ModelSpec(provider=Provider.CODEX, model_name="gpt-5.4"),
    )

    assert settings.for_stage(StageType.DEFAULT) is default
