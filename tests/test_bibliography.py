"""Tests for writing.bibliography — BibTeX and Markdown bibliography loading."""

from __future__ import annotations

from pathlib import Path

import pytest
from writing.bibliography import Bibliography

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def bib_from_bibtex() -> Bibliography:
    """Load the sample .bib fixture."""
    return Bibliography().load(FIXTURES_DIR / "sample.bib")


@pytest.fixture
def bib_from_markdown() -> Bibliography:
    """Load the sample Markdown bibliography fixture."""
    return Bibliography().load(FIXTURES_DIR / "sample_bibliography.md")


# ---------------------------------------------------------------------------
# BibTeX loading
# ---------------------------------------------------------------------------


class TestBibTexLoading:
    """Test loading .bib files."""

    def test_loads_correct_count(self, bib_from_bibtex) -> None:
        assert len(bib_from_bibtex) == 3

    def test_entry_keys(self, bib_from_bibtex) -> None:
        assert "vaswani2017attention" in bib_from_bibtex
        assert "devlin2019bert" in bib_from_bibtex
        assert "goodfellow2016deep" in bib_from_bibtex

    def test_entry_fields(self, bib_from_bibtex) -> None:
        entry = bib_from_bibtex.get("vaswani2017attention")
        assert entry is not None
        assert entry.title == "Attention Is All You Need"
        assert entry.year == 2017
        assert "Vaswani" in entry.authors

    def test_missing_year_defaults_to_zero(self, tmp_path) -> None:
        bib_file = tmp_path / "noyear.bib"
        bib_file.write_text(
            "@article{noyear2024,\n"
            "  title={No Year Article},\n"
            "  author={Doe, John},\n"
            "}\n"
        )
        bib = Bibliography().load(bib_file)
        entry = bib.get("noyear2024")
        assert entry is not None
        assert entry.year == 0

    def test_empty_bib_file(self, tmp_path) -> None:
        bib_file = tmp_path / "empty.bib"
        bib_file.write_text("")
        bib = Bibliography().load(bib_file)
        assert len(bib) == 0

    def test_source_type_from_entry_type(self, bib_from_bibtex) -> None:
        entry = bib_from_bibtex.get("goodfellow2016deep")
        assert entry is not None
        assert entry.source_type == "book"


# ---------------------------------------------------------------------------
# Markdown loading
# ---------------------------------------------------------------------------


class TestMarkdownLoading:
    """Test loading structured Markdown bibliography files."""

    def test_loads_correct_count(self, bib_from_markdown) -> None:
        assert len(bib_from_markdown) == 3

    def test_entry_keys(self, bib_from_markdown) -> None:
        assert "vaswani2017" in bib_from_markdown
        assert "devlin2019" in bib_from_markdown
        assert "brown2020" in bib_from_markdown

    def test_entry_fields(self, bib_from_markdown) -> None:
        entry = bib_from_markdown.get("brown2020")
        assert entry is not None
        assert "Few-Shot Learners" in entry.title
        assert entry.year == 2020

    def test_source_type_from_markdown(self, bib_from_markdown) -> None:
        entry = bib_from_markdown.get("vaswani2017")
        assert entry is not None
        assert entry.source_type == "NeurIPS"


# ---------------------------------------------------------------------------
# Lookup helpers and protocols
# ---------------------------------------------------------------------------


class TestLookups:
    """Test contains, get, __contains__, and auto-detection."""

    def test_contains_method(self, bib_from_bibtex) -> None:
        assert bib_from_bibtex.contains("vaswani2017attention") is True
        assert bib_from_bibtex.contains("nonexistent") is False

    def test_get_missing_returns_none(self, bib_from_bibtex) -> None:
        assert bib_from_bibtex.get("nonexistent") is None

    def test_dunder_contains(self, bib_from_bibtex) -> None:
        assert "devlin2019bert" in bib_from_bibtex
        assert "nope" not in bib_from_bibtex

    def test_dunder_contains_non_string(self, bib_from_bibtex) -> None:
        assert 42 not in bib_from_bibtex

    def test_iter_protocol(self, bib_from_bibtex) -> None:
        entries = list(bib_from_bibtex)
        assert len(entries) == 3

    def test_keys_property(self, bib_from_bibtex) -> None:
        keys = bib_from_bibtex.keys
        assert isinstance(keys, list)
        assert len(keys) == 3

    def test_load_auto_detects_bib(self) -> None:
        bib = Bibliography().load(FIXTURES_DIR / "sample.bib")
        assert len(bib) == 3

    def test_load_auto_detects_md(self) -> None:
        bib = Bibliography().load(FIXTURES_DIR / "sample_bibliography.md")
        assert len(bib) == 3

    def test_load_unsupported_extension_raises(self, tmp_path) -> None:
        bad_file = tmp_path / "refs.txt"
        bad_file.write_text("some content")
        with pytest.raises(ValueError, match="Unsupported bibliography format"):
            Bibliography().load(bad_file)
