"""Unit tests for writing.prompt_assembler."""

from __future__ import annotations

import pytest
from writing.bibliography import Bibliography
from writing.models import (
    CitationEntry,
    ContentType,
    FewShotExample,
    StyleProfile,
)
from writing.prompt_assembler import (
    AssembledPrompt,
    _estimate_tokens,
    _format_bibliography_hints,
    _format_outline_context,
    _format_style_profile,
    _truncate_to_tokens,
    assemble_prompt,
)
from writing.settings import WriterSettings

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_bibliography(*entries: tuple[str, str, str, int]) -> Bibliography:
    """Build a Bibliography with the given (key, title, authors, year) tuples."""
    bib = Bibliography()
    for key, title, authors, year in entries:
        bib._entries[key] = CitationEntry(
            key=key,
            title=title,
            authors=authors,
            year=year,
        )
    return bib


def _make_style_profile() -> StyleProfile:
    """Build a representative StyleProfile for testing."""
    return StyleProfile(
        vocabulary_level="advanced",
        tone="formal academic",
        paragraph_structure="topic-evidence-conclusion",
        sentence_patterns=["compound-complex sentences", "passive voice for results"],
        opening_patterns=["thematic statement", "research question"],
        closing_patterns=["summary + future work"],
        structural_conventions=["numbered headings", "footnotes for asides"],
    )


@pytest.fixture
def settings(tmp_path) -> WriterSettings:
    """WriterSettings with a temporary cache directory."""
    return WriterSettings(cache_dir=tmp_path)


# ---------------------------------------------------------------------------
# _estimate_tokens
# ---------------------------------------------------------------------------


class TestEstimateTokens:
    """Tests for the _estimate_tokens helper."""

    def test_empty_string(self) -> None:
        assert _estimate_tokens("") == 0

    def test_single_word(self) -> None:
        result = _estimate_tokens("hello")
        assert result >= 1

    def test_reasonable_estimate(self) -> None:
        text = "This is a short sentence with seven words total roughly."
        tokens = _estimate_tokens(text)
        word_count = len(text.split())
        # Should be roughly word_count * 1.3
        assert tokens == int(word_count * 1.3)

    def test_returns_integer(self) -> None:
        assert isinstance(_estimate_tokens("some text here"), int)


# ---------------------------------------------------------------------------
# _truncate_to_tokens
# ---------------------------------------------------------------------------


class TestTruncateToTokens:
    """Tests for _truncate_to_tokens."""

    def test_short_text_unchanged(self) -> None:
        text = "Short text."
        assert _truncate_to_tokens(text, 1000) == text

    def test_empty_text(self) -> None:
        assert _truncate_to_tokens("", 100) == ""

    def test_long_text_truncated(self) -> None:
        text = " ".join(f"word{i}" for i in range(500))
        result = _truncate_to_tokens(text, 10)
        assert "[... truncated ...]" in result
        assert _estimate_tokens(result) <= 10

    def test_truncated_text_shorter_than_original(self) -> None:
        text = " ".join(f"w{i}" for i in range(200))
        result = _truncate_to_tokens(text, 20)
        assert len(result) < len(text)


# ---------------------------------------------------------------------------
# _format_style_profile
# ---------------------------------------------------------------------------


class TestFormatStyleProfile:
    """Tests for _format_style_profile."""

    def test_includes_all_fields(self) -> None:
        profile = _make_style_profile()
        output = _format_style_profile(profile, max_tokens=5000)

        assert "Vocabulary Level: advanced" in output
        assert "Tone: formal academic" in output
        assert "Paragraph Structure: topic-evidence-conclusion" in output
        assert "Sentence Patterns:" in output
        assert "compound-complex sentences" in output
        assert "Opening Patterns:" in output
        assert "Closing Patterns:" in output
        assert "Structural Conventions:" in output

    def test_empty_profile(self) -> None:
        profile = StyleProfile()
        output = _format_style_profile(profile, max_tokens=5000)
        # Empty profile produces empty string
        assert output == ""

    def test_truncation_under_budget(self) -> None:
        profile = _make_style_profile()
        output = _format_style_profile(profile, max_tokens=5)
        assert "[... truncated ...]" in output


# ---------------------------------------------------------------------------
# _format_bibliography_hints
# ---------------------------------------------------------------------------


class TestFormatBibliographyHints:
    """Tests for _format_bibliography_hints."""

    def test_lists_citation_keys(self) -> None:
        bib = _make_bibliography(
            ("smith2020", "Deep Learning Advances", "Smith, J.", 2020),
            ("jones2021", "Transformer Architectures", "Jones, A.", 2021),
        )
        output = _format_bibliography_hints(bib, max_tokens=5000)

        assert "Available citations:" in output
        assert "smith2020" in output
        assert "jones2021" in output
        assert "Deep Learning Advances" in output
        assert "Smith, J." in output

    def test_empty_bibliography(self) -> None:
        bib = Bibliography()
        output = _format_bibliography_hints(bib, max_tokens=5000)
        assert "No bibliography provided" in output


# ---------------------------------------------------------------------------
# _format_outline_context
# ---------------------------------------------------------------------------


class TestFormatOutlineContext:
    """Tests for _format_outline_context."""

    def test_marks_current_section(self) -> None:
        outline = ["Introduction", "Methods", "Results", "Discussion"]
        output = _format_outline_context(outline, "Methods")
        assert "Document Outline:" in output
        # Current section should have ">>" marker
        assert ">> 2. Methods" in output
        # Other sections should have spaces
        assert "   1. Introduction" in output
        assert "   3. Results" in output

    def test_empty_outline(self) -> None:
        output = _format_outline_context([], "Methods")
        assert "No outline available" in output

    def test_no_current_section_match(self) -> None:
        outline = ["Intro", "Body", "Conclusion"]
        output = _format_outline_context(outline, "NonExistent")
        # All should have spaces, none with ">>"
        assert ">>" not in output


# ---------------------------------------------------------------------------
# assemble_prompt (integration of all components)
# ---------------------------------------------------------------------------


class TestAssemblePrompt:
    """Tests for the top-level assemble_prompt function."""

    def test_with_all_components(self, settings, tmp_path) -> None:
        profile = _make_style_profile()
        bib = _make_bibliography(
            ("key1", "Title One", "Author A", 2020),
        )
        example_file = tmp_path / "example.md"
        example_file.write_text("Example academic paragraph.")
        examples = [
            FewShotExample(
                source_path=example_file,
                content="Example academic paragraph.",
                section_slice="Introduction",
                token_count=5,
            ),
        ]
        outline = ["Introduction", "Methods", "Results"]

        result = assemble_prompt(
            content_type=ContentType.PAPER,
            instruction="Write about neural networks",
            section_name="Introduction",
            style_profile=profile,
            few_shot_examples=examples,
            running_context="Previously generated text.",
            bibliography=bib,
            outline=outline,
            settings=settings,
        )

        assert isinstance(result, AssembledPrompt)
        assert "neural networks" in result.user_prompt
        assert "Introduction" in result.user_prompt
        assert result.total_tokens > 0
        assert "style_profile" in result.budget_report
        assert "few_shot_examples" in result.budget_report
        assert "running_context" in result.budget_report
        assert "bibliography_hints" in result.budget_report
        assert "outline" in result.budget_report
        assert "total" in result.budget_report

    def test_with_minimal_components(self, settings) -> None:
        result = assemble_prompt(
            content_type=ContentType.PAPER,
            instruction="Minimal test",
            settings=settings,
        )
        assert isinstance(result, AssembledPrompt)
        assert "Minimal test" in result.user_prompt
        assert result.total_tokens > 0
        # Fallback text for missing components
        assert "No style profile provided" in result.user_prompt
        assert "No prior context" in result.user_prompt
        assert "No bibliography provided" in result.user_prompt
        assert "No outline available" in result.user_prompt

    def test_token_budget_enforcement(self, settings) -> None:
        # Use a very small style profile budget
        settings.token_budgets.style_profile = 5
        profile = _make_style_profile()
        # Add lots of text to sentence_patterns to inflate the profile
        profile.sentence_patterns = [f"pattern number {i} with extra words" for i in range(100)]

        result = assemble_prompt(
            content_type=ContentType.PAPER,
            instruction="budget test",
            style_profile=profile,
            settings=settings,
        )
        # The style_profile token count in the budget should be at or under the limit
        assert result.budget_report["style_profile"] <= 5

    def test_budget_report_keys(self, settings) -> None:
        result = assemble_prompt(
            content_type=ContentType.PAPER,
            instruction="keys test",
            settings=settings,
        )
        expected_keys = {
            "style_profile",
            "few_shot_examples",
            "running_context",
            "bibliography_hints",
            "outline",
            "total",
        }
        assert expected_keys == set(result.budget_report.keys())
