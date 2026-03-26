"""Tests for writing.style — style response parsing and prompt building."""

from __future__ import annotations

import pytest
from writing.style import _build_analysis_prompt, _extract_section, _parse_style_response

# ---------------------------------------------------------------------------
# _parse_style_response
# ---------------------------------------------------------------------------


class TestParseStyleResponse:
    """Test parsing a structured LLM response into StyleProfile fields."""

    @pytest.fixture
    def well_formed_response(self) -> str:
        """A well-formed style analysis response with all expected sections."""
        return (
            "### VOCABULARY LEVEL\n"
            "Advanced academic vocabulary with domain-specific terminology.\n"
            "\n"
            "### SENTENCE PATTERNS\n"
            "- Long compound-complex sentences\n"
            "- Frequent use of passive voice\n"
            "- Parenthetical asides for clarification\n"
            "\n"
            "### PARAGRAPH STRUCTURE\n"
            "Paragraphs average 4-6 sentences. Topic sentences lead, "
            "followed by supporting evidence and a transition.\n"
            "\n"
            "### TONE\n"
            "Formal and authoritative with measured analytical stance.\n"
            "\n"
            "### OPENING PATTERNS\n"
            "- Broad contextual statement\n"
            "- Defining the problem space\n"
            "\n"
            "### CLOSING PATTERNS\n"
            "- Summary of key findings\n"
            "- Forward-looking implications\n"
            "\n"
            "### STRUCTURAL CONVENTIONS\n"
            "- Numbered sections with descriptive headings\n"
            "- In-text citations in author-year format\n"
        )

    def test_vocabulary_level_parsed(self, well_formed_response) -> None:
        profile = _parse_style_response(well_formed_response)
        assert "academic" in profile.vocabulary_level.lower()

    def test_sentence_patterns_parsed(self, well_formed_response) -> None:
        profile = _parse_style_response(well_formed_response)
        assert len(profile.sentence_patterns) >= 2
        assert any("passive" in p.lower() for p in profile.sentence_patterns)

    def test_paragraph_structure_parsed(self, well_formed_response) -> None:
        profile = _parse_style_response(well_formed_response)
        assert "topic sentence" in profile.paragraph_structure.lower()

    def test_tone_parsed(self, well_formed_response) -> None:
        profile = _parse_style_response(well_formed_response)
        assert "formal" in profile.tone.lower()

    def test_opening_patterns_parsed(self, well_formed_response) -> None:
        profile = _parse_style_response(well_formed_response)
        assert len(profile.opening_patterns) >= 1

    def test_closing_patterns_parsed(self, well_formed_response) -> None:
        profile = _parse_style_response(well_formed_response)
        assert len(profile.closing_patterns) >= 1

    def test_structural_conventions_parsed(self, well_formed_response) -> None:
        profile = _parse_style_response(well_formed_response)
        assert len(profile.structural_conventions) >= 1

    def test_raw_analysis_preserved(self, well_formed_response) -> None:
        profile = _parse_style_response(well_formed_response)
        assert profile.raw_analysis == well_formed_response


class TestParseStyleResponseMissingSections:
    """Test parsing when sections are missing from the response."""

    def test_empty_response(self) -> None:
        profile = _parse_style_response("")
        assert profile.vocabulary_level == ""
        assert profile.sentence_patterns == []
        assert profile.tone == ""

    def test_partial_response(self) -> None:
        partial = (
            "### VOCABULARY LEVEL\n"
            "Simple conversational tone.\n"
        )
        profile = _parse_style_response(partial)
        assert "conversational" in profile.vocabulary_level.lower()
        # Missing sections default to empty.
        assert profile.sentence_patterns == []
        assert profile.tone == ""


# ---------------------------------------------------------------------------
# _extract_section (style module's version)
# ---------------------------------------------------------------------------


class TestExtractSection:
    """Test the style-module section extractor."""

    def test_extract_existing_section(self) -> None:
        text = "### TONE\nFormal and measured.\n\n### VOCABULARY LEVEL\nAdvanced.\n"
        result = _extract_section(text, "TONE")
        assert "Formal" in result

    def test_extract_missing_section(self) -> None:
        text = "### TONE\nFormal.\n"
        result = _extract_section(text, "PARAGRAPH STRUCTURE")
        assert result == ""


# ---------------------------------------------------------------------------
# _build_analysis_prompt
# ---------------------------------------------------------------------------


class TestBuildAnalysisPrompt:
    """Test prompt construction from the style_analysis.md template."""

    def test_includes_corpus_text(self) -> None:
        corpus_text = "Sample corpus content for analysis."
        prompt = _build_analysis_prompt(corpus_text)
        assert corpus_text in prompt

    def test_includes_section_headers(self) -> None:
        prompt = _build_analysis_prompt("dummy text")
        assert "VOCABULARY LEVEL" in prompt
        assert "SENTENCE PATTERNS" in prompt
        assert "TONE" in prompt

    def test_template_placeholder_replaced(self) -> None:
        prompt = _build_analysis_prompt("my custom text")
        assert "{{ corpus_text }}" not in prompt
