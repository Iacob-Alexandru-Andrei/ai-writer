"""Style analysis module for the ai-writer system.

Analyzes a user's writing corpus via an LLM to extract a ``StyleProfile``
capturing vocabulary level, sentence patterns, tone, and structural
conventions.  An optional spaCy path computes additional quantitative
metrics when the library is available.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from writing.backends import LLMBackend, get_backend
from writing.models import StyleProfile

if TYPE_CHECKING:
    from writing.corpus import Corpus

_TEMPLATE_DIR: Path = Path(__file__).resolve().parent.parent.parent / "templates"
"""Resolved path to the project ``templates/`` directory."""

_MAX_CORPUS_WORDS: int = 10_000
"""Maximum number of words to include in the analysis prompt."""


def analyze_style(
    corpus: Corpus,
    backend: LLMBackend | None = None,
) -> StyleProfile:
    """Analyze a writing corpus and return a structured style profile.

    Concatenates the normalized content of every file in *corpus* (truncated
    to roughly ``_MAX_CORPUS_WORDS`` words), sends the text to an LLM using
    the ``style_analysis.md`` prompt template, and parses the structured
    response into a ``StyleProfile``.

    Args:
        corpus: A loaded ``Corpus`` instance containing at least one file.
        backend: LLM backend to use for the analysis call.  When *None*,
            ``get_backend()`` selects the default backend.

    Returns:
        A ``StyleProfile`` populated from the LLM analysis.
    """
    if backend is None:
        backend = get_backend()

    corpus_text = _concatenate_corpus(corpus)
    prompt = _build_analysis_prompt(corpus_text)
    response = backend.generate(prompt)
    profile = _parse_style_response(response)

    # Optionally enrich with quantitative spaCy metrics.
    spacy_metrics = _compute_spacy_metrics(corpus_text)
    if spacy_metrics:
        profile.raw_analysis += f"\n\n--- spaCy metrics ---\n{spacy_metrics!r}"

    return profile


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _concatenate_corpus(corpus: Corpus) -> str:
    """Join all corpus files, truncated to ``_MAX_CORPUS_WORDS`` words.

    Args:
        corpus: A loaded ``Corpus`` instance.

    Returns:
        A single string of concatenated, truncated corpus content.
    """
    parts: list[str] = []
    word_budget = _MAX_CORPUS_WORDS

    for cf in corpus.files:
        words = cf.normalized_content.split()
        if word_budget <= 0:
            break
        if len(words) > word_budget:
            words = words[:word_budget]
        parts.append(" ".join(words))
        word_budget -= len(words)

    return "\n\n---\n\n".join(parts)


def _build_analysis_prompt(corpus_text: str) -> str:
    """Read the ``style_analysis.md`` template and substitute the corpus text.

    Args:
        corpus_text: Concatenated (and possibly truncated) corpus text.

    Returns:
        The fully rendered prompt string ready for LLM submission.
    """
    template_path = _TEMPLATE_DIR / "style_analysis.md"
    template = template_path.read_text(encoding="utf-8")
    return template.replace("{{ corpus_text }}", corpus_text)


def _parse_list_items(block: str) -> list[str]:
    """Extract bullet-list items from a text block.

    Recognises lines starting with ``-`` or ``*``.  Falls back to splitting
    on newlines when no bullets are found.

    Args:
        block: Raw text block from which to extract items.

    Returns:
        A list of trimmed, non-empty strings.
    """
    items = re.findall(r"^[\-\*]\s+(.+)", block, re.MULTILINE)
    if items:
        return [item.strip() for item in items if item.strip()]
    # Fallback: split on newlines and keep non-empty lines.
    return [line.strip() for line in block.strip().splitlines() if line.strip()]


def _extract_section(text: str, header: str) -> str:
    """Extract the text between *header* and the next section header.

    Section headers are lines that start with ``###`` or are fully
    upper-cased labels.  The search is case-insensitive.

    Args:
        text: The full LLM response text.
        header: The section header to locate (e.g. ``"VOCABULARY LEVEL"``).

    Returns:
        The content of the section, or an empty string if not found.
    """
    # Match the header (possibly preceded by ### or similar).
    escaped = re.escape(header)
    header_prefix = r"(?:#{1,4}\s*)?"
    pattern = (
        r"(?:^|\n)" + header_prefix + escaped + r"\s*\n"
        r"(.*?)(?=\n" + header_prefix + r"[A-Z][A-Z ]+\s*\n|\Z)"
    )
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def _parse_style_response(response: str) -> StyleProfile:
    """Parse a structured LLM response into a ``StyleProfile``.

    Expects the response to contain clearly labeled sections matching the
    headers defined in ``style_analysis.md``.

    Args:
        response: The raw text returned by the LLM.

    Returns:
        A ``StyleProfile`` with fields populated from the parsed sections.
    """
    vocabulary_block = _extract_section(response, "VOCABULARY LEVEL")
    sentence_block = _extract_section(response, "SENTENCE PATTERNS")
    paragraph_block = _extract_section(response, "PARAGRAPH STRUCTURE")
    tone_block = _extract_section(response, "TONE")
    opening_block = _extract_section(response, "OPENING PATTERNS")
    closing_block = _extract_section(response, "CLOSING PATTERNS")
    structural_block = _extract_section(response, "STRUCTURAL CONVENTIONS")

    return StyleProfile(
        vocabulary_level=vocabulary_block,
        sentence_patterns=_parse_list_items(sentence_block),
        paragraph_structure=paragraph_block,
        tone=tone_block,
        opening_patterns=_parse_list_items(opening_block),
        closing_patterns=_parse_list_items(closing_block),
        structural_conventions=_parse_list_items(structural_block),
        raw_analysis=response,
    )


def _compute_spacy_metrics(corpus_text: str) -> dict[str, object]:
    """Compute quantitative style metrics using spaCy, if available.

    Calculates POS-tag distributions, average sentence length, and
    type-token ratio.  Returns an empty dict when spaCy is not installed
    or fails to load.

    Args:
        corpus_text: The concatenated corpus text to analyze.

    Returns:
        A dictionary of metric names to values, or an empty dict if
        spaCy is unavailable.
    """
    try:
        import spacy  # noqa: PLC0415  # ty: ignore[unresolved-import]
    except ImportError:
        return {}

    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        return {}

    # Process a truncated slice to keep spaCy fast.
    max_chars = 50_000
    doc = nlp(corpus_text[:max_chars])

    # POS distribution.
    pos_counts: dict[str, int] = {}
    for token in doc:
        pos_counts[token.pos_] = pos_counts.get(token.pos_, 0) + 1
    total_tokens = len(doc) or 1
    pos_distribution = {pos: count / total_tokens for pos, count in pos_counts.items()}

    # Average sentence length.
    sentences = list(doc.sents)
    avg_sentence_length = (
        sum(len(sent) for sent in sentences) / len(sentences) if sentences else 0.0
    )

    # Type-token ratio (vocabulary richness).
    unique_tokens = {token.lower_ for token in doc if token.is_alpha}
    alpha_tokens = [token for token in doc if token.is_alpha]
    type_token_ratio = len(unique_tokens) / len(alpha_tokens) if alpha_tokens else 0.0

    return {
        "pos_distribution": pos_distribution,
        "avg_sentence_length": round(avg_sentence_length, 2),
        "type_token_ratio": round(type_token_ratio, 4),
        "total_sentences": len(sentences),
    }
