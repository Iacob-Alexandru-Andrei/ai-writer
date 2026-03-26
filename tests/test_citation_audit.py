"""Unit tests for writing.citation_audit."""

from __future__ import annotations

from writing.bibliography import Bibliography
from writing.citation_audit import (
    CitationAuditResult,
    audit_citations,
    extract_citation_keys,
    format_audit_report,
)
from writing.models import CitationEntry

# ---------------------------------------------------------------------------
# Helpers
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


# ---------------------------------------------------------------------------
# extract_citation_keys -- LaTeX
# ---------------------------------------------------------------------------


class TestExtractLatexCitations:
    r"""Tests for LaTeX citation extraction (\cite, \citep, \citet)."""

    def test_cite_single(self) -> None:
        text = r"As shown in \cite{smith2020}, the method works."
        keys = extract_citation_keys(text)
        assert keys == ["smith2020"]

    def test_citep_single(self) -> None:
        text = r"Results confirm this \citep{jones2021}."
        keys = extract_citation_keys(text)
        assert keys == ["jones2021"]

    def test_citet_single(self) -> None:
        text = r"\citet{brown2019} proposed a novel approach."
        keys = extract_citation_keys(text)
        assert keys == ["brown2019"]

    def test_cite_multiple_keys(self) -> None:
        text = r"Prior work \cite{alpha2020,beta2021} covers this."
        keys = extract_citation_keys(text)
        assert "alpha2020" in keys
        assert "beta2021" in keys

    def test_citep_multiple_keys(self) -> None:
        text = r"Supported by \citep{a1,b2,c3} in the literature."
        keys = extract_citation_keys(text)
        assert len(keys) == 3
        assert "a1" in keys
        assert "b2" in keys
        assert "c3" in keys

    def test_deduplicates(self) -> None:
        text = r"\cite{key1} and also \cite{key1} again."
        keys = extract_citation_keys(text)
        assert keys == ["key1"]


# ---------------------------------------------------------------------------
# extract_citation_keys -- Markdown
# ---------------------------------------------------------------------------


class TestExtractMarkdownCitations:
    """Tests for Markdown citation extraction ([@key] style)."""

    def test_single_key(self) -> None:
        text = "As noted [@smith2020], the results hold."
        keys = extract_citation_keys(text)
        assert keys == ["smith2020"]

    def test_multiple_keys_semicolon(self) -> None:
        text = "Various studies [@alpha2020; @beta2021] show this."
        keys = extract_citation_keys(text)
        assert "alpha2020" in keys
        assert "beta2021" in keys

    def test_deduplicates_across_formats(self) -> None:
        text = r"See \cite{key1} and also [@key1]."
        keys = extract_citation_keys(text)
        assert keys.count("key1") == 1


# ---------------------------------------------------------------------------
# extract_citation_keys -- edge cases
# ---------------------------------------------------------------------------


class TestExtractEdgeCases:
    """Edge cases for extract_citation_keys."""

    def test_no_citations(self) -> None:
        text = "This is plain text with no citations at all."
        keys = extract_citation_keys(text)
        assert keys == []

    def test_empty_string(self) -> None:
        keys = extract_citation_keys("")
        assert keys == []

    def test_inline_citation(self) -> None:
        text = "As shown by (Smith, 2020), the hypothesis holds."
        keys = extract_citation_keys(text)
        assert "Smith, 2020" in keys

    def test_inline_et_al(self) -> None:
        text = "According to (Johnson et al., 2019), this is true."
        keys = extract_citation_keys(text)
        assert "Johnson et al., 2019" in keys

    def test_mixed_formats(self) -> None:
        text = (
            r"We follow \cite{latex_key} and also [@md_key]. "
            "Additionally (Author, 2021) confirmed."
        )
        keys = extract_citation_keys(text)
        assert "latex_key" in keys
        assert "md_key" in keys
        assert "Author, 2021" in keys


# ---------------------------------------------------------------------------
# audit_citations
# ---------------------------------------------------------------------------


class TestAuditCitations:
    """Tests for audit_citations."""

    def test_all_verified(self) -> None:
        bib = _make_bibliography(
            ("smith2020", "Paper A", "Smith", 2020),
            ("jones2021", "Paper B", "Jones", 2021),
        )
        text = r"See \cite{smith2020} and \cite{jones2021}."
        result = audit_citations(text, bib)

        assert isinstance(result, CitationAuditResult)
        assert result.total_citations == 2
        assert len(result.verified) == 2
        assert len(result.unknown) == 0
        assert "smith2020" in result.verified
        assert "jones2021" in result.verified

    def test_some_unknown(self) -> None:
        bib = _make_bibliography(
            ("smith2020", "Paper A", "Smith", 2020),
        )
        text = r"\cite{smith2020} and \cite{unknown_key}."
        result = audit_citations(text, bib)

        assert result.total_citations == 2
        assert len(result.verified) == 1
        assert len(result.unknown) == 1
        assert "unknown_key" in result.unknown

    def test_all_unknown(self) -> None:
        bib = Bibliography()
        text = r"\cite{ghost1} and [@ghost2]."
        result = audit_citations(text, bib)

        assert result.total_citations == 2
        assert len(result.verified) == 0
        assert len(result.unknown) == 2

    def test_no_citations(self) -> None:
        bib = _make_bibliography(("smith2020", "Paper A", "Smith", 2020))
        text = "No citations in this text."
        result = audit_citations(text, bib)

        assert result.total_citations == 0
        assert result.verified == []
        assert result.unknown == []

    def test_inline_citation_fuzzy_match(self) -> None:
        bib = _make_bibliography(
            ("smith2020deep", "Deep Learning", "Smith, J.", 2020),
        )
        text = "As shown by (Smith, 2020), the method works."
        result = audit_citations(text, bib)

        # The inline pseudo-key "Smith, 2020" should fuzzy-match against
        # the entry with authors "Smith, J." and year 2020
        assert result.total_citations == 1
        assert len(result.verified) == 1

    def test_inline_citation_no_match(self) -> None:
        bib = _make_bibliography(
            ("jones2019", "Other Paper", "Jones, A.", 2019),
        )
        text = "According to (Smith, 2020), the hypothesis holds."
        result = audit_citations(text, bib)

        assert result.total_citations == 1
        assert len(result.unknown) == 1


# ---------------------------------------------------------------------------
# format_audit_report
# ---------------------------------------------------------------------------


class TestFormatAuditReport:
    """Tests for format_audit_report."""

    def test_produces_readable_output(self) -> None:
        bib = _make_bibliography(
            ("smith2020", "Paper A", "Smith", 2020),
        )
        result = CitationAuditResult(
            verified=["smith2020"],
            unknown=["ghost_key"],
            total_citations=2,
        )
        report = format_audit_report(result, bib)

        assert "Citation Audit Report" in report
        assert "Total unique citations: 2" in report
        assert "Verified: 1" in report
        assert "Unknown:  1" in report
        assert "[OK] smith2020" in report
        assert "Paper A" in report
        assert "[??] ghost_key" in report
        assert "NOT FOUND" in report

    def test_all_verified_report(self) -> None:
        bib = _make_bibliography(
            ("a", "Title A", "Auth A", 2020),
            ("b", "Title B", "Auth B", 2021),
        )
        result = CitationAuditResult(
            verified=["a", "b"],
            unknown=[],
            total_citations=2,
        )
        report = format_audit_report(result, bib)

        assert "Verified: 2" in report
        assert "Unknown:  0" in report
        assert "[??]" not in report

    def test_empty_result_report(self) -> None:
        bib = Bibliography()
        result = CitationAuditResult(
            verified=[],
            unknown=[],
            total_citations=0,
        )
        report = format_audit_report(result, bib)

        assert "Total unique citations: 0" in report
        assert "Verified: 0" in report
        assert "Unknown:  0" in report

    def test_inline_pseudo_key_in_report(self) -> None:
        bib = Bibliography()
        result = CitationAuditResult(
            verified=["Smith, 2020"],
            unknown=[],
            total_citations=1,
        )
        report = format_audit_report(result, bib)

        # Inline pseudo-keys have no direct entry, so appear without title
        assert "[OK] Smith, 2020" in report
