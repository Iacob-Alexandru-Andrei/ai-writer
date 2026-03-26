"""Tests for writing.corpus — Corpus loading, search, and LaTeX normalization."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from writing.corpus import Corpus, _normalize_latex_regex, normalize_latex

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SAMPLE_CORPUS_DIR = FIXTURES_DIR / "sample_corpus"


@pytest.fixture
def corpus_md(tmp_path: Path) -> Corpus:
    """Corpus containing only Markdown files."""
    (tmp_path / "doc1.md").write_text("# Title\n\nHello world content here.")
    (tmp_path / "doc2.md").write_text("# Another\n\nSome different text about testing.")
    return Corpus(tmp_path).load()


@pytest.fixture
def corpus_tex(tmp_path: Path) -> Corpus:
    r"""Corpus containing a single .tex file."""
    tex = (
        "\\section{Intro}\n"
        "Some \\textbf{bold} text.\n"
        "\\begin{itemize}\n"
        "Item one\n"
        "\\end{itemize}\n"
    )
    (tmp_path / "paper.tex").write_text(tex)
    return Corpus(tmp_path).load()


@pytest.fixture
def corpus_sample() -> Corpus:
    """Corpus loaded from the shared test fixtures (paper1.md + paper2.tex)."""
    return Corpus(SAMPLE_CORPUS_DIR).load()


# ---------------------------------------------------------------------------
# Loading tests
# ---------------------------------------------------------------------------


class TestCorpusLoading:
    """Test Corpus.load() behaviour for various directory contents."""

    def test_load_md_files(self, corpus_md) -> None:
        assert len(corpus_md) == 2
        names = {f.source_path.name for f in corpus_md}
        assert names == {"doc1.md", "doc2.md"}

    def test_md_files_are_markdown_format(self, corpus_md) -> None:
        for f in corpus_md:
            assert f.format == "markdown"

    def test_load_tex_files(self, corpus_tex) -> None:
        assert len(corpus_tex) == 1
        assert corpus_tex.files[0].format == "latex"

    def test_tex_normalized_content_is_not_raw(self, corpus_tex) -> None:
        cf = corpus_tex.files[0]
        # Normalized content should not contain \section or \textbf.
        assert "\\section" not in cf.normalized_content
        assert "\\textbf" not in cf.normalized_content

    def test_empty_directory(self, tmp_path) -> None:
        corpus = Corpus(tmp_path).load()
        assert len(corpus) == 0
        assert corpus.files == []

    def test_nonexistent_directory_raises(self, tmp_path) -> None:
        missing = tmp_path / "nonexistent"
        with pytest.raises(FileNotFoundError):
            Corpus(missing).load()

    def test_word_count_populated(self, corpus_md) -> None:
        for f in corpus_md:
            assert f.word_count > 0

    def test_sample_fixtures_load(self, corpus_sample) -> None:
        assert len(corpus_sample) == 2
        formats = {f.format for f in corpus_sample}
        assert formats == {"markdown", "latex"}


# ---------------------------------------------------------------------------
# Accessor tests
# ---------------------------------------------------------------------------


class TestCorpusAccessors:
    """Test search, get_file, and iteration."""

    def test_search_finds_matching_files(self, corpus_md) -> None:
        results = corpus_md.search("testing")
        assert len(results) == 1
        assert results[0].source_path.name == "doc2.md"

    def test_search_case_insensitive(self, corpus_md) -> None:
        results = corpus_md.search("HELLO")
        assert len(results) == 1

    def test_search_no_match(self, corpus_md) -> None:
        assert corpus_md.search("zzzznotfound") == []

    def test_get_file_by_name(self, corpus_md) -> None:
        cf = corpus_md.get_file("doc1.md")
        assert cf is not None
        assert cf.source_path.name == "doc1.md"

    def test_get_file_missing_returns_none(self, corpus_md) -> None:
        assert corpus_md.get_file("nonexistent.md") is None

    def test_iter_protocol(self, corpus_md) -> None:
        names = [f.source_path.name for f in corpus_md]
        assert len(names) == 2

    def test_total_words(self, corpus_md) -> None:
        assert corpus_md.total_words > 0


# ---------------------------------------------------------------------------
# expose_for_grep
# ---------------------------------------------------------------------------


class TestExposeForGrep:
    """Test Corpus.expose_for_grep() file creation."""

    def test_creates_md_files(self, corpus_sample, tmp_path) -> None:
        target = tmp_path / "grep_dir"
        corpus_sample.expose_for_grep(target)

        created = sorted(p.name for p in target.iterdir())
        assert "paper1.md" in created
        assert "paper2.md" in created  # .tex stem gets .md extension

    def test_created_files_are_readable(self, corpus_sample, tmp_path) -> None:
        target = tmp_path / "grep_dir"
        corpus_sample.expose_for_grep(target)
        for md_file in target.iterdir():
            text = md_file.read_text()
            assert len(text) > 0


# ---------------------------------------------------------------------------
# normalize_latex (regex fallback)
# ---------------------------------------------------------------------------


class TestNormalizeLatex:
    """Test the regex-based LaTeX normalization path."""

    def test_section_to_heading(self) -> None:
        result = _normalize_latex_regex(r"\section{My Section}")
        assert "## My Section" in result

    def test_subsection_to_heading(self) -> None:
        result = _normalize_latex_regex(r"\subsection{Sub}")
        assert "### Sub" in result

    def test_textbf_to_bold(self) -> None:
        result = _normalize_latex_regex(r"\textbf{bold text}")
        assert "**bold text**" in result

    def test_textit_to_italic(self) -> None:
        result = _normalize_latex_regex(r"\textit{italic text}")
        assert "*italic text*" in result

    def test_begin_end_stripped(self) -> None:
        result = _normalize_latex_regex(
            "\\begin{document}\nContent here\n\\end{document}"
        )
        assert "\\begin" not in result
        assert "\\end" not in result
        assert "Content here" in result

    def test_chapter_to_h1(self) -> None:
        result = _normalize_latex_regex(r"\chapter{Ch}")
        assert "# Ch" in result

    def test_texttt_to_code(self) -> None:
        result = _normalize_latex_regex(r"\texttt{code}")
        assert "`code`" in result

    def test_excessive_blank_lines_collapsed(self) -> None:
        result = _normalize_latex_regex("a\n\n\n\n\nb")
        assert "\n\n\n" not in result

    def test_normalize_latex_uses_regex_when_pandoc_missing(self) -> None:
        """Ensure normalize_latex falls back to regex when pandoc is absent."""
        with patch("writing.corpus._check_pandoc_available", return_value=False):
            result = normalize_latex(r"\section{Fallback}")
            assert "## Fallback" in result
