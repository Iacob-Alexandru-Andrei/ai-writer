"""Integration tests exercising the full Pipeline for all five content types.

All LLM calls are mocked -- these tests verify pipeline wiring, data flow,
session state transitions, and persistence, not generation quality.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from writing.backends import LLMBackend
from writing.models import ContentType, GenerationResult, SessionStatus
from writing.pipeline import Pipeline
from writing.settings import WriterSettings
from writing.workflows.long_form import LongFormWorkflow
from writing.workflows.short_form import ShortFormWorkflow

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_STYLE_ANALYSIS_RESPONSE = (
    "VOCABULARY LEVEL\n"
    "Advanced academic vocabulary with domain-specific terminology.\n\n"
    "SENTENCE PATTERNS\n"
    "- Complex compound sentences with subordinate clauses\n"
    "- Frequent use of passive voice in methods sections\n\n"
    "PARAGRAPH STRUCTURE\n"
    "Topic sentence followed by evidence and analysis.\n\n"
    "TONE\n"
    "Formal and objective.\n\n"
    "OPENING PATTERNS\n"
    "- Broad context statement narrowing to specific focus\n\n"
    "CLOSING PATTERNS\n"
    "- Summary of key findings with future directions\n\n"
    "STRUCTURAL CONVENTIONS\n"
    "- Clear section headings\n"
    "- Numbered lists for methodology steps\n"
)

_OUTLINE_RESPONSE = (
    "1. Introduction\n"
    "2. Methods\n"
    "3. Results\n"
    "4. Discussion\n"
)

_SECTION_CONTENT = (
    "This section presents detailed findings from our analysis. "
    "The transformer architecture demonstrated superior performance "
    "across all benchmarks. We observed a significant improvement "
    "in accuracy when using attention mechanisms compared to "
    "traditional recurrent approaches."
)

_SHORT_FORM_CONTENT = (
    "AI is transforming how we work.\n\n"
    "Here are 3 key insights from my research:\n\n"
    "1. Automation is not replacement\n"
    "2. Human-AI collaboration outperforms either alone\n"
    "3. The best teams adapt their workflows\n\n"
    "What has been your experience? #AI #FutureOfWork"
)

_TWITTER_CONTENT = (
    "Thread on AI and the future of work:\n\n"
    "1/ AI is not here to replace us. "
    "It is here to augment our capabilities."
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def corpus_dir(tmp_path: Path) -> Path:
    """Create a temporary corpus directory with sample files."""
    src = FIXTURES_DIR / "sample_corpus"
    dest = tmp_path / "corpus"
    shutil.copytree(src, dest)
    return dest


@pytest.fixture
def bib_path(tmp_path: Path) -> Path:
    """Copy the sample .bib file into a temp location."""
    src = FIXTURES_DIR / "sample.bib"
    dest = tmp_path / "refs.bib"
    shutil.copy2(src, dest)
    return dest


@pytest.fixture
def mock_backend() -> MagicMock:
    """Return a MagicMock that satisfies the LLMBackend interface."""
    backend = MagicMock(spec=LLMBackend)
    backend.generate.return_value = _SECTION_CONTENT
    return backend


@pytest.fixture
def settings(tmp_path: Path) -> WriterSettings:
    """Return WriterSettings with cache_dir pointed at a temp directory."""
    return WriterSettings(cache_dir=tmp_path / "sessions")


@pytest.fixture
def pipeline(mock_backend: MagicMock, settings: WriterSettings) -> Pipeline:
    """Return a Pipeline wired to the mock backend and temp settings."""
    return Pipeline(backend=mock_backend, settings=settings)


# ===================================================================
# Long-form workflow tests (paper, thesis, blog)
# ===================================================================


class TestLongFormPaper:
    """End-to-end pipeline test for ContentType.PAPER."""

    def test_full_lifecycle(
        self,
        pipeline: Pipeline,
        mock_backend: MagicMock,
        corpus_dir: Path,
        bib_path: Path,
    ) -> None:
        """Walk through start -> outline -> generate -> status -> finalize."""
        # Configure mock to return style analysis, then outline, then sections.
        mock_backend.generate.side_effect = [
            _STYLE_ANALYSIS_RESPONSE,  # style analysis in start_session
            _OUTLINE_RESPONSE,         # outline generation
            _SECTION_CONTENT,          # section 1: Introduction
            _SECTION_CONTENT,          # section 2: Methods
        ]

        # 1. Start session
        session = pipeline.start_session(
            content_type=ContentType.PAPER,
            instruction="Write a survey on neural architectures",
            corpus_dir=corpus_dir,
            bibliography_path=bib_path,
        )
        assert session.status == SessionStatus.ANALYZING
        assert session.style_profile is not None
        assert session.content_type == ContentType.PAPER

        # 2. Generate outline
        outline = pipeline.generate_outline(session)
        assert len(outline) >= 2
        assert session.status == SessionStatus.OUTLINING
        assert session.outline == outline

        # 3. Generate first section
        result1 = pipeline.generate_next(session)
        assert isinstance(result1, GenerationResult)
        assert result1.content == _SECTION_CONTENT
        assert session.status == SessionStatus.GENERATING
        assert session.current_section_index == 1
        assert len(session.sections) == 1

        # 4. Generate second section
        result2 = pipeline.generate_next(session)
        assert isinstance(result2, GenerationResult)
        assert session.current_section_index == 2
        assert len(session.sections) == 2

        # 5. Check status
        status = pipeline.get_status(session)
        assert status["completed_sections"] == 2
        assert status["status"] == "generating"
        assert "outline" in status

        # 6. Finalize (generate remaining sections first by resetting side_effect)
        # For finalize we need all sections done -- skip remaining and finalize directly.
        mock_backend.generate.side_effect = None
        mock_backend.generate.return_value = _SECTION_CONTENT
        # Generate the remaining sections to completion.
        while session.current_section_index < len(session.outline):
            pipeline.generate_next(session)

        final_doc = pipeline.finalize(session)
        assert session.status == SessionStatus.COMPLETE
        assert isinstance(final_doc, str)
        assert len(final_doc) > 0
        # Final document should contain section headers.
        assert "## " in final_doc


class TestLongFormThesis:
    """End-to-end pipeline test for ContentType.THESIS."""

    def test_thesis_lifecycle(
        self,
        pipeline: Pipeline,
        mock_backend: MagicMock,
        corpus_dir: Path,
    ) -> None:
        mock_backend.generate.side_effect = [
            _STYLE_ANALYSIS_RESPONSE,  # style analysis
            "1. Introduction\n2. Literature Review\n3. Conclusion",  # outline
            _SECTION_CONTENT,  # section 1
            _SECTION_CONTENT,  # section 2
            _SECTION_CONTENT,  # section 3
        ]

        session = pipeline.start_session(
            content_type=ContentType.THESIS,
            instruction="Thesis on attention mechanisms",
            corpus_dir=corpus_dir,
        )
        assert session.content_type == ContentType.THESIS
        assert session.status == SessionStatus.ANALYZING

        outline = pipeline.generate_outline(session)
        assert len(outline) == 3
        assert session.status == SessionStatus.OUTLINING

        # Generate all sections.
        for _ in range(len(outline)):
            result = pipeline.generate_next(session)
            assert isinstance(result, GenerationResult)

        assert session.current_section_index == 3
        assert session.status == SessionStatus.GENERATING

        final_doc = pipeline.finalize(session)
        assert session.status == SessionStatus.COMPLETE
        assert "## Introduction" in final_doc
        assert "## Conclusion" in final_doc


class TestLongFormBlog:
    """End-to-end pipeline test for ContentType.BLOG."""

    def test_blog_lifecycle(
        self,
        pipeline: Pipeline,
        mock_backend: MagicMock,
        corpus_dir: Path,
    ) -> None:
        mock_backend.generate.side_effect = [
            _STYLE_ANALYSIS_RESPONSE,
            "1. Hook and Introduction\n2. Key Insights\n3. Takeaways",
            _SECTION_CONTENT,
            _SECTION_CONTENT,
            _SECTION_CONTENT,
        ]

        session = pipeline.start_session(
            content_type=ContentType.BLOG,
            instruction="Blog post about transformer models",
            corpus_dir=corpus_dir,
        )
        assert session.content_type == ContentType.BLOG
        assert session.status == SessionStatus.ANALYZING
        assert session.style_profile is not None

        outline = pipeline.generate_outline(session)
        assert len(outline) == 3

        for _ in range(len(outline)):
            pipeline.generate_next(session)

        status = pipeline.get_status(session)
        assert status["completed_sections"] == 3
        assert status["total_sections"] == 3

        final_doc = pipeline.finalize(session)
        assert session.status == SessionStatus.COMPLETE
        assert len(final_doc) > 0


# ===================================================================
# Short-form workflow tests (linkedin, twitter)
# ===================================================================


class TestShortFormLinkedIn:
    """End-to-end pipeline test for ContentType.LINKEDIN."""

    def test_linkedin_lifecycle(
        self,
        pipeline: Pipeline,
        mock_backend: MagicMock,
    ) -> None:
        mock_backend.generate.return_value = _SHORT_FORM_CONTENT

        # 1. Start session (no corpus required).
        session = pipeline.start_session(
            content_type=ContentType.LINKEDIN,
            instruction="Write about AI in the workplace",
        )
        assert session.content_type == ContentType.LINKEDIN
        assert session.status == SessionStatus.ANALYZING

        # 2. Generate content.
        result = pipeline.generate_next(session)
        assert isinstance(result, GenerationResult)
        assert result.content == _SHORT_FORM_CONTENT
        assert session.status == SessionStatus.REVIEWING

        # 3. Check status.
        status = pipeline.get_status(session)
        assert status["content_type"] == "linkedin"
        assert status["status"] == "reviewing"
        assert status["has_result"] is True

        # 4. Finalize.
        final = pipeline.finalize(session)
        assert session.status == SessionStatus.COMPLETE
        assert final == _SHORT_FORM_CONTENT

    def test_linkedin_with_corpus(
        self,
        pipeline: Pipeline,
        mock_backend: MagicMock,
        corpus_dir: Path,
    ) -> None:
        """LinkedIn can optionally accept a corpus for style analysis."""
        mock_backend.generate.side_effect = [
            _STYLE_ANALYSIS_RESPONSE,  # style analysis
            _SHORT_FORM_CONTENT,       # content generation
        ]

        session = pipeline.start_session(
            content_type=ContentType.LINKEDIN,
            instruction="AI insights post",
            corpus_dir=corpus_dir,
        )
        assert session.content_type == ContentType.LINKEDIN
        assert session.style_profile is not None

        result = pipeline.generate_next(session)
        assert isinstance(result, GenerationResult)


class TestShortFormTwitter:
    """End-to-end pipeline test for ContentType.TWITTER."""

    def test_twitter_lifecycle(
        self,
        pipeline: Pipeline,
        mock_backend: MagicMock,
    ) -> None:
        mock_backend.generate.return_value = _TWITTER_CONTENT

        session = pipeline.start_session(
            content_type=ContentType.TWITTER,
            instruction="Thread on AI and future of work",
        )
        assert session.content_type == ContentType.TWITTER
        assert session.status == SessionStatus.ANALYZING

        result = pipeline.generate_next(session)
        assert isinstance(result, GenerationResult)
        assert result.content == _TWITTER_CONTENT

        status = pipeline.get_status(session)
        assert status["content_type"] == "twitter"
        assert status["has_result"] is True

        final = pipeline.finalize(session)
        assert session.status == SessionStatus.COMPLETE
        assert final == _TWITTER_CONTENT


# ===================================================================
# Pipeline routing tests
# ===================================================================


class TestPipelineRouting:
    """Verify that content types route to the correct workflow."""

    def test_paper_routes_to_long_form(self, pipeline: Pipeline) -> None:
        workflow = pipeline._get_workflow(ContentType.PAPER)
        assert isinstance(workflow, LongFormWorkflow)

    def test_thesis_routes_to_long_form(self, pipeline: Pipeline) -> None:
        workflow = pipeline._get_workflow(ContentType.THESIS)
        assert isinstance(workflow, LongFormWorkflow)

    def test_blog_routes_to_long_form(self, pipeline: Pipeline) -> None:
        workflow = pipeline._get_workflow(ContentType.BLOG)
        assert isinstance(workflow, LongFormWorkflow)

    def test_linkedin_routes_to_short_form(self, pipeline: Pipeline) -> None:
        workflow = pipeline._get_workflow(ContentType.LINKEDIN)
        assert isinstance(workflow, ShortFormWorkflow)

    def test_twitter_routes_to_short_form(self, pipeline: Pipeline) -> None:
        workflow = pipeline._get_workflow(ContentType.TWITTER)
        assert isinstance(workflow, ShortFormWorkflow)

    def test_is_long_form_classification(self) -> None:
        assert Pipeline._is_long_form(ContentType.PAPER) is True
        assert Pipeline._is_long_form(ContentType.THESIS) is True
        assert Pipeline._is_long_form(ContentType.BLOG) is True
        assert Pipeline._is_long_form(ContentType.LINKEDIN) is False
        assert Pipeline._is_long_form(ContentType.TWITTER) is False

    def test_outline_rejects_short_form(
        self,
        pipeline: Pipeline,
        mock_backend: MagicMock,
    ) -> None:
        """generate_outline() should raise ValueError for short-form types."""
        mock_backend.generate.return_value = _SHORT_FORM_CONTENT
        session = pipeline.start_session(
            content_type=ContentType.LINKEDIN,
            instruction="Post about AI",
        )
        with pytest.raises(ValueError, match=r"short-form|long-form|Outline"):
            pipeline.generate_outline(session)

    def test_long_form_requires_corpus(self, pipeline: Pipeline) -> None:
        """start_session for long-form types must receive corpus_dir."""
        with pytest.raises(ValueError, match="corpus_dir"):
            pipeline.start_session(
                content_type=ContentType.PAPER,
                instruction="No corpus provided",
            )


# ===================================================================
# Session persistence tests
# ===================================================================


class TestSessionPersistence:
    """Verify that sessions survive save/load round-trips mid-workflow."""

    def test_resume_session_preserves_state(
        self,
        pipeline: Pipeline,
        mock_backend: MagicMock,
        corpus_dir: Path,
    ) -> None:
        """Start a session, advance it, then resume by ID and verify state."""
        mock_backend.generate.side_effect = [
            _STYLE_ANALYSIS_RESPONSE,
            _OUTLINE_RESPONSE,
            _SECTION_CONTENT,
        ]

        # Start and advance.
        session = pipeline.start_session(
            content_type=ContentType.PAPER,
            instruction="Persistence test paper",
            corpus_dir=corpus_dir,
        )
        session_id = session.session_id

        pipeline.generate_outline(session)
        pipeline.generate_next(session)

        # Resume from disk.
        resumed = pipeline.resume_session(session_id)

        assert resumed.session_id == session_id
        assert resumed.content_type == ContentType.PAPER
        assert resumed.instruction == "Persistence test paper"
        assert resumed.status == SessionStatus.GENERATING
        assert len(resumed.outline) >= 2
        assert resumed.current_section_index == 1
        assert len(resumed.sections) == 1
        assert resumed.sections[0].content == _SECTION_CONTENT

    def test_resume_nonexistent_raises(self, pipeline: Pipeline) -> None:
        with pytest.raises(FileNotFoundError):
            pipeline.resume_session("nonexistent_session_id_12345")

    def test_list_sessions_after_creation(
        self,
        pipeline: Pipeline,
        mock_backend: MagicMock,
    ) -> None:
        mock_backend.generate.return_value = _SHORT_FORM_CONTENT

        pipeline.start_session(
            content_type=ContentType.LINKEDIN,
            instruction="Post one",
        )
        pipeline.start_session(
            content_type=ContentType.TWITTER,
            instruction="Thread one",
        )

        listing = pipeline.list_sessions()
        assert len(listing) == 2
        instructions = {item["instruction"] for item in listing}
        assert instructions == {"Post one", "Thread one"}


# ===================================================================
# State transition tests
# ===================================================================


class TestStateTransitions:
    """Verify that session status follows the expected lifecycle."""

    def test_long_form_state_sequence(
        self,
        pipeline: Pipeline,
        mock_backend: MagicMock,
        corpus_dir: Path,
    ) -> None:
        """ANALYZING -> OUTLINING -> GENERATING -> COMPLETE."""
        mock_backend.generate.side_effect = [
            _STYLE_ANALYSIS_RESPONSE,
            "1. Introduction\n2. Conclusion",
            _SECTION_CONTENT,
            _SECTION_CONTENT,
        ]

        session = pipeline.start_session(
            content_type=ContentType.PAPER,
            instruction="State transitions test",
            corpus_dir=corpus_dir,
        )
        assert session.status == SessionStatus.ANALYZING

        pipeline.generate_outline(session)
        assert session.status == SessionStatus.OUTLINING

        pipeline.generate_next(session)
        assert session.status == SessionStatus.GENERATING

        pipeline.generate_next(session)
        assert session.status == SessionStatus.GENERATING

        pipeline.finalize(session)
        assert session.status == SessionStatus.COMPLETE

    def test_short_form_state_sequence(
        self,
        pipeline: Pipeline,
        mock_backend: MagicMock,
    ) -> None:
        """ANALYZING -> REVIEWING -> COMPLETE."""
        mock_backend.generate.return_value = _SHORT_FORM_CONTENT

        session = pipeline.start_session(
            content_type=ContentType.LINKEDIN,
            instruction="Short-form state test",
        )
        assert session.status == SessionStatus.ANALYZING

        pipeline.generate_next(session)
        assert session.status == SessionStatus.REVIEWING

        pipeline.finalize(session)
        assert session.status == SessionStatus.COMPLETE


# ===================================================================
# Edge cases
# ===================================================================


class TestEdgeCases:
    """Edge-case and error-path tests."""

    def test_generate_past_outline_raises(
        self,
        pipeline: Pipeline,
        mock_backend: MagicMock,
        corpus_dir: Path,
    ) -> None:
        """Generating beyond all outline sections should raise IndexError."""
        mock_backend.generate.side_effect = [
            _STYLE_ANALYSIS_RESPONSE,
            "1. Only Section",
            _SECTION_CONTENT,
        ]

        session = pipeline.start_session(
            content_type=ContentType.PAPER,
            instruction="Overflow test",
            corpus_dir=corpus_dir,
        )
        pipeline.generate_outline(session)
        pipeline.generate_next(session)  # generates the single section

        with pytest.raises(IndexError):
            pipeline.generate_next(session)

    def test_finalize_short_form_without_content_raises(
        self,
        pipeline: Pipeline,
        mock_backend: MagicMock,
    ) -> None:
        """Finalizing before generating should raise ValueError."""
        mock_backend.generate.return_value = _SHORT_FORM_CONTENT
        session = pipeline.start_session(
            content_type=ContentType.LINKEDIN,
            instruction="No content yet",
        )
        with pytest.raises(ValueError, match="no content"):
            pipeline.finalize(session)

    @patch(
        "writing.workflows.long_form.StormAdapter.is_available",
        return_value=False,
    )
    def test_outline_falls_back_without_storm(
        self,
        mock_storm_available,
        pipeline: Pipeline,
        mock_backend: MagicMock,
        corpus_dir: Path,
    ) -> None:
        """Outline should work via LLM fallback when STORM is unavailable."""
        mock_backend.generate.side_effect = [
            _STYLE_ANALYSIS_RESPONSE,
            _OUTLINE_RESPONSE,
        ]

        session = pipeline.start_session(
            content_type=ContentType.PAPER,
            instruction="No STORM test",
            corpus_dir=corpus_dir,
        )
        outline = pipeline.generate_outline(session)
        assert len(outline) >= 2
        assert session.status == SessionStatus.OUTLINING
        assert mock_storm_available.called
