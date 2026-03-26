"""Tests for writing.fewshot — few-shot example selection and helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from writing.corpus import Corpus
from writing.fewshot import (
    _estimate_tokens,
    _extract_section,
    _truncate_to_budget,
    select_examples,
    suggest_examples,
)
from writing.settings import TokenBudgets, WriterSettings

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def corpus(tmp_path: Path) -> Corpus:
    """Build a small corpus with three files for testing selection."""
    (tmp_path / "intro.md").write_text(
        "## Introduction\n\n"
        "This is the introduction section with some content about neural networks. "
        + "Word " * 100
    )
    (tmp_path / "methods.md").write_text(
        "## Methods\n\n"
        "We used transformer architectures for all experiments. "
        + "Word " * 100
    )
    (tmp_path / "results.md").write_text(
        "## Results\n\n"
        "The results show significant improvement. "
        + "Word " * 100
    )
    return Corpus(tmp_path).load()


@pytest.fixture
def large_corpus(tmp_path: Path) -> Corpus:
    """Build a corpus with files large enough to trigger truncation."""
    # Each file is roughly 5000 words -> ~6500 tokens.
    for name in ["big1.md", "big2.md", "big3.md", "big4.md"]:
        (tmp_path / name).write_text("Word " * 5000)
    return Corpus(tmp_path).load()


# ---------------------------------------------------------------------------
# _estimate_tokens
# ---------------------------------------------------------------------------


class TestEstimateTokens:
    """Test the token estimation heuristic."""

    def test_empty_string(self) -> None:
        assert _estimate_tokens("") == 0

    def test_short_text(self) -> None:
        tokens = _estimate_tokens("Hello world")
        assert tokens > 0

    def test_longer_text_higher_estimate(self) -> None:
        short = _estimate_tokens("Hello")
        long = _estimate_tokens("Hello world this is a longer sentence with more words")
        assert long > short

    def test_returns_max_of_two_heuristics(self) -> None:
        text = "a " * 100
        word_est = int(len(text.split()) * 1.3)
        char_est = len(text) // 4
        assert _estimate_tokens(text) == max(word_est, char_est)


# ---------------------------------------------------------------------------
# _extract_section
# ---------------------------------------------------------------------------


class TestExtractSection:
    """Test Markdown section slicing."""

    def test_extract_existing_section(self) -> None:
        content = "## Intro\n\nIntro text here.\n\n## Methods\n\nMethods text."
        result = _extract_section(content, "Intro")
        assert result is not None
        assert "Intro text here" in result

    def test_extract_stops_at_next_heading(self) -> None:
        content = "## Intro\n\nIntro text.\n\n## Methods\n\nMethods text."
        result = _extract_section(content, "Intro")
        assert result is not None
        assert "Methods text" not in result

    def test_extract_missing_section_returns_none(self) -> None:
        content = "## Intro\n\nSome text."
        assert _extract_section(content, "Nonexistent") is None

    def test_extract_case_insensitive(self) -> None:
        content = "## RESULTS\n\nResult data here."
        result = _extract_section(content, "results")
        assert result is not None
        assert "Result data" in result

    def test_extract_h3_section(self) -> None:
        content = "### Details\n\nDetail text.\n\n### Other\n\nOther."
        result = _extract_section(content, "Details")
        assert result is not None
        assert "Detail text" in result


# ---------------------------------------------------------------------------
# _truncate_to_budget
# ---------------------------------------------------------------------------


class TestTruncateToBudget:
    """Test the truncation helper."""

    def test_no_truncation_when_within_budget(self) -> None:
        text = "Short text."
        result, was_truncated = _truncate_to_budget(text, 1000)
        assert result == text
        assert was_truncated is False

    def test_truncation_when_over_budget(self) -> None:
        text = "Word " * 2000
        result, was_truncated = _truncate_to_budget(text, 100)
        assert was_truncated is True
        assert "[... truncated ...]" in result
        assert _estimate_tokens(result) <= 100


# ---------------------------------------------------------------------------
# select_examples
# ---------------------------------------------------------------------------


class TestSelectExamples:
    """Test select_examples with various configurations."""

    def test_select_named_files(self, corpus) -> None:
        examples = select_examples(corpus, ["intro.md", "methods.md"])
        assert len(examples) == 2
        names = {e.source_path.name for e in examples}
        assert names == {"intro.md", "methods.md"}

    def test_skip_missing_file(self, corpus) -> None:
        examples = select_examples(corpus, ["intro.md", "nonexistent.md"])
        assert len(examples) == 1

    def test_max_3_examples_enforced(self, corpus) -> None:
        # Default max is 3; requesting 3 files should work.
        examples = select_examples(
            corpus, ["intro.md", "methods.md", "results.md"]
        )
        assert len(examples) <= 3

    def test_max_examples_custom_setting(self, corpus) -> None:
        settings = WriterSettings(max_fewshot_examples=1)
        examples = select_examples(
            corpus, ["intro.md", "methods.md", "results.md"], settings=settings
        )
        assert len(examples) == 1

    def test_truncation_under_per_example_budget(self, large_corpus) -> None:
        settings = WriterSettings(
            token_budgets=TokenBudgets(fewshot_per_example=50, fewshot_total=100000),
        )
        examples = select_examples(large_corpus, ["big1.md"], settings=settings)
        assert len(examples) == 1
        assert _estimate_tokens(examples[0].content) <= 50

    def test_total_budget_enforced(self, large_corpus) -> None:
        settings = WriterSettings(
            token_budgets=TokenBudgets(
                fewshot_per_example=100000,
                fewshot_total=100,
            ),
        )
        examples = select_examples(
            large_corpus, ["big1.md", "big2.md"], settings=settings
        )
        total_tokens = sum(e.token_count for e in examples)
        assert total_tokens <= 100

    def test_section_slicing(self, corpus) -> None:
        examples = select_examples(
            corpus, ["intro.md"], section="Introduction"
        )
        assert len(examples) == 1
        assert examples[0].section_slice == "Introduction"


# ---------------------------------------------------------------------------
# suggest_examples
# ---------------------------------------------------------------------------


class TestSuggestExamples:
    """Test suggest_examples returns names without auto-selecting."""

    def test_returns_relevant_names(self, corpus) -> None:
        suggestions = suggest_examples(corpus, "neural networks")
        assert isinstance(suggestions, list)
        # "intro.md" mentions "neural networks"
        assert "intro.md" in suggestions

    def test_returns_no_more_than_max(self, corpus) -> None:
        suggestions = suggest_examples(corpus, "content", max_suggestions=2)
        assert len(suggestions) <= 2

    def test_empty_instruction(self, corpus) -> None:
        suggestions = suggest_examples(corpus, "")
        assert suggestions == []

    def test_no_matches(self, corpus) -> None:
        suggestions = suggest_examples(corpus, "zzzzzzzzz")
        assert suggestions == []
