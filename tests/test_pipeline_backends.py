"""Integration tests for per-stage backend wiring, session persistence, and backward compat."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from writing.backends import ClaudeCLIBackend, FallbackBackend, LLMBackend, resolve_backend
from writing.llm_config import LLMSettings, ModelSpec, OutlineEngine, Provider, StageType
from writing.models import SessionState
from writing.pipeline import Pipeline
from writing.prompt_assembler import assemble_prompt
from writing.session import SessionManager
from writing.settings import WriterSettings, load_settings


class _MockBackend(LLMBackend):
    """Simple mock backend that returns a fixed string."""

    def __init__(self, name: str = "mock") -> None:
        self.name = name
        self.calls: list[str] = []

    def generate(self, prompt: str, system: str | None = None) -> str:
        self.calls.append(prompt[:50])
        return f"Response from {self.name}"

    def generate_structured(self, prompt: str, schema: type) -> object:
        return schema()


# ------------------------------------------------------------------
# Per-stage backend resolution
# ------------------------------------------------------------------


def test_resolve_backend_for_stage_returns_fallback():
    """resolve_backend returns a FallbackBackend for any stage."""
    settings = LLMSettings(
        default=ModelSpec(provider=Provider.CLAUDE, model_name="opus-4.6"),
    )
    backend = resolve_backend(StageType.SECTION_GENERATION, settings)
    assert isinstance(backend, FallbackBackend)


def test_resolve_backend_uses_stage_override():
    """When a stage has its own ModelSpec, resolve_backend uses it."""
    settings = LLMSettings(
        default=ModelSpec(provider=Provider.CLAUDE, model_name="opus-4.6"),
        style_analysis=ModelSpec(provider=Provider.CODEX, model_name="gpt-5.4"),
    )
    backend = resolve_backend(StageType.STYLE_ANALYSIS, settings)
    assert isinstance(backend, FallbackBackend)
    # Primary should be CodexBackend since style_analysis overrides to codex
    from writing.backends import CodexBackend

    assert isinstance(backend.primary, CodexBackend)


def test_resolve_backend_falls_back_to_default():
    """When a stage has no override, resolve_backend uses the default."""
    settings = LLMSettings(
        default=ModelSpec(provider=Provider.CLAUDE, model_name="opus-4.6"),
    )
    backend = resolve_backend(StageType.OUTLINE, settings)
    assert isinstance(backend, FallbackBackend)
    assert isinstance(backend.primary, ClaudeCLIBackend)


# ------------------------------------------------------------------
# Pipeline backward compat
# ------------------------------------------------------------------


def test_pipeline_explicit_backend_bypasses_resolution():
    """Pipeline(backend=X) uses X for all stages, no resolution."""
    mock = _MockBackend("explicit")
    p = Pipeline(backend=mock)
    # Internal resolver should return the explicit backend
    assert p._resolve_backend_for_stage(StageType.STYLE_ANALYSIS) is mock
    assert p._resolve_backend_for_stage(StageType.SECTION_GENERATION) is mock
    assert p._resolve_backend_for_stage(StageType.OUTLINE) is mock


def test_pipeline_without_backend_resolves_per_stage():
    """Pipeline() without explicit backend uses resolve_backend per stage."""
    p = Pipeline()
    # Should return a FallbackBackend for each stage
    style_be = p._resolve_backend_for_stage(StageType.STYLE_ANALYSIS)
    section_be = p._resolve_backend_for_stage(StageType.SECTION_GENERATION)
    assert isinstance(style_be, FallbackBackend)
    assert isinstance(section_be, FallbackBackend)


# ------------------------------------------------------------------
# Session LLM snapshot persistence
# ------------------------------------------------------------------


def test_session_round_trip_preserves_llm_settings(tmp_path: Path):
    """LLMSettings survives save/load cycle."""
    settings = WriterSettings(cache_dir=tmp_path)
    sm = SessionManager(settings=settings)

    llm = LLMSettings(
        default=ModelSpec(provider=Provider.CODEX, model_name="gpt-5.4"),
        section_generation=ModelSpec(
            provider=Provider.CLAUDE,
            model_name="opus-4.6",
            max_output_tokens=32768,
        ),
        outline_engine=OutlineEngine.LLM,
    )

    session = sm.create(
        content_type="paper",
        instruction="test",
        llm_settings=llm,
    )
    sm.save(session)

    loaded = sm.load(session.session_id)
    assert loaded.llm_settings is not None
    assert loaded.llm_settings.default.provider == Provider.CODEX
    assert loaded.llm_settings.default.model_name == "gpt-5.4"
    assert loaded.llm_settings.section_generation is not None
    assert loaded.llm_settings.section_generation.model_name == "opus-4.6"
    assert loaded.llm_settings.section_generation.max_output_tokens == 32768
    assert loaded.llm_settings.outline_engine == OutlineEngine.LLM


def test_session_without_llm_settings_loads_fine(tmp_path: Path):
    """Sessions created before this feature (no llm_settings) load correctly."""
    settings = WriterSettings(cache_dir=tmp_path)
    sm = SessionManager(settings=settings)

    session = sm.create(content_type="paper", instruction="test")
    # Explicitly set to None to simulate old session
    session.llm_settings = None
    sm.save(session)

    loaded = sm.load(session.session_id)
    assert loaded.llm_settings is None


# ------------------------------------------------------------------
# Prompt budget integration
# ------------------------------------------------------------------


def test_prompt_budget_with_custom_context_length():
    """assemble_prompt respects context_length and max_output_tokens."""
    from writing.models import ContentType

    result = assemble_prompt(
        content_type=ContentType.PAPER,
        instruction="Write about AI",
        section_name="Introduction",
        context_length=200000,
        max_output_tokens=16384,
    )
    # The prompt should have been assembled (not error)
    assert result.user_prompt
    assert result.total_tokens > 0


def test_prompt_budget_without_limits_uses_defaults():
    """assemble_prompt without context_length/max_output_tokens works as before."""
    from writing.models import ContentType

    result = assemble_prompt(
        content_type=ContentType.PAPER,
        instruction="Write about AI",
        section_name="Introduction",
    )
    assert result.user_prompt
    assert result.total_tokens > 0


# ------------------------------------------------------------------
# Outline engine selection
# ------------------------------------------------------------------


def test_outline_engine_llm_bypasses_storm():
    """When outline_engine=llm, STORM is never called even if available."""
    from writing.workflows.long_form import LongFormWorkflow

    mock_be = _MockBackend("outline")
    # Make mock backend return a numbered list that parses to outline sections
    mock_be.generate = lambda prompt, system=None: "1. Introduction\n2. Methods\n3. Results"

    mock_sm = MagicMock(spec=SessionManager)
    settings = WriterSettings()
    settings.llm.outline_engine = OutlineEngine.LLM

    wf = LongFormWorkflow(session_manager=mock_sm, backend=mock_be, settings=settings)

    with patch("writing.workflows.long_form.StormAdapter") as mock_storm:
        mock_storm.is_available.return_value = True

        from writing.models import ContentType as CT

        session = MagicMock(spec=SessionState)
        session.session_id = "test-outline"
        session.content_type = CT.PAPER
        session.instruction = "Test topic"
        session.corpus_dir = None
        session.style_profile = None

        # Mock corpus loading to avoid file I/O
        with patch.object(wf, "_load_corpus") as mock_corpus:
            mock_corpus_obj = MagicMock()
            mock_corpus_obj.files = []
            mock_corpus.return_value = mock_corpus_obj

            outline = wf.generate_outline(session)

        # STORM should NOT have been called
        mock_storm.assert_not_called()
        # Outline should have been generated via LLM
        assert len(outline) > 0
        assert "Introduction" in outline[0]


# ------------------------------------------------------------------
# Config precedence in load_settings
# ------------------------------------------------------------------


def test_llm_overrides_in_load_settings(tmp_path: Path):
    """CLI llm_overrides take precedence over YAML."""
    yaml_file = tmp_path / "settings.yaml"
    yaml_file.write_text("model:\n  default:\n    provider: auto\n    model_name: haiku\n")

    settings = load_settings(
        path=yaml_file,
        llm_overrides={"provider": "codex", "model": "gpt-5.4"},
    )
    assert settings.llm.default.provider == Provider.CODEX
    assert settings.llm.default.model_name == "gpt-5.4"
