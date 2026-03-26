"""Few-shot example selection and extraction from a user corpus.

Provides helpers to look up, slice, truncate, and budget-gate reference
examples that are included in generation prompts so the LLM can mimic
the author's style.  Per SPEC R04, files are **never** silently chosen;
the user explicitly names them and this module only *suggests*.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from writing.models import FewShotExample
from writing.settings import WriterSettings

if TYPE_CHECKING:
    from writing.corpus import Corpus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

_CHARS_PER_TOKEN = 4
"""Rough characters-per-token constant used by :func:`_estimate_tokens`."""


def _estimate_tokens(text: str) -> int:
    """Return a rough token estimate for *text*.

    Uses the larger of two heuristics -- ``words * 1.3`` and
    ``len(text) / 4`` -- so the budget errs on the conservative side.

    Args:
        text: Arbitrary string.

    Returns:
        Estimated token count (always >= 0).
    """
    word_estimate = int(len(text.split()) * 1.3)
    char_estimate = len(text) // _CHARS_PER_TOKEN
    return max(word_estimate, char_estimate)


# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------

_TRUNCATION_MARKER = "\n\n[... truncated ...]"


def _truncate_to_budget(text: str, max_tokens: int) -> tuple[str, bool]:
    """Truncate *text* so its estimated token count stays within *max_tokens*.

    If truncation is necessary the returned string ends with a
    ``[... truncated ...]`` marker so the LLM knows content was removed.

    Args:
        text: Source text.
        max_tokens: Upper token budget.

    Returns:
        A ``(text, was_truncated)`` tuple.
    """
    if _estimate_tokens(text) <= max_tokens:
        return text, False

    # Binary-search-ish: progressively shorten by words until we fit.
    words = text.split()
    lo, hi = 0, len(words)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        candidate = " ".join(words[:mid]) + _TRUNCATION_MARKER
        if _estimate_tokens(candidate) <= max_tokens:
            lo = mid
        else:
            hi = mid - 1

    truncated = " ".join(words[:lo]) + _TRUNCATION_MARKER
    return truncated, True


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------

# Matches ``## Heading`` or ``### Heading`` lines (with optional leading ``#``s).
_HEADING_RE = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)


def _extract_section(content: str, section_name: str) -> str | None:
    """Extract the text under a Markdown heading matching *section_name*.

    Looks for ``##`` or ``###`` headings whose text matches
    *section_name* (case-insensitive).  The returned slice spans from
    the line after the heading up to (but not including) the next heading
    of the same or higher level, or the end of the document.

    Args:
        content: Full Markdown document text.
        section_name: Heading text to search for.

    Returns:
        The section body as a string, or ``None`` if no matching heading
        was found.
    """
    target = section_name.strip().lower()

    matches = list(_HEADING_RE.finditer(content))
    for idx, match in enumerate(matches):
        heading_level = len(match.group(1))
        heading_text = match.group(2).strip().lower()

        if heading_text != target:
            continue

        # Start of body: right after the heading line.
        body_start = match.end()

        # End of body: next heading at same-or-higher level, or EOF.
        body_end = len(content)
        for subsequent in matches[idx + 1 :]:
            subsequent_level = len(subsequent.group(1))
            if subsequent_level <= heading_level:
                body_end = subsequent.start()
                break

        return content[body_start:body_end].strip()

    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def select_examples(
    corpus: Corpus,
    file_names: list[str],
    *,
    settings: WriterSettings | None = None,
    section: str | None = None,
) -> list[FewShotExample]:
    """Build a list of few-shot examples from explicitly named corpus files.

    Per SPEC R04 the caller (user) **explicitly** selects which files to
    include.  This function looks them up, optionally slices to a
    specific section, truncates to budget, and enforces the maximum
    example count and total token budget.

    Args:
        corpus: A loaded :class:`~writing.corpus.Corpus`.
        file_names: Filenames (not full paths) to pull from the corpus.
        settings: Optional settings override; defaults are used when ``None``.
        section: If given, only the content under this heading is extracted
            from each file.

    Returns:
        A list of :class:`~writing.models.FewShotExample` instances that
        fit within the configured budgets.
    """
    cfg = settings or WriterSettings()
    per_example_budget = cfg.token_budgets.fewshot_per_example
    total_budget = cfg.token_budgets.fewshot_total
    max_examples = cfg.max_fewshot_examples

    examples: list[FewShotExample] = []
    running_tokens = 0

    for name in file_names:
        if len(examples) >= max_examples:
            logger.debug("Reached max_fewshot_examples (%d), stopping.", max_examples)
            break

        cf = corpus.get_file(name)
        if cf is None:
            logger.warning("Corpus file not found: %s — skipping.", name)
            continue

        text = cf.normalized_content
        section_slice: str | None = None

        if section is not None:
            extracted = _extract_section(text, section)
            if extracted is not None:
                text = extracted
                section_slice = section
            else:
                logger.debug(
                    "Section '%s' not found in %s — using full content.",
                    section,
                    name,
                )

        text, was_truncated = _truncate_to_budget(text, per_example_budget)
        if was_truncated:
            logger.debug("Truncated %s to %d-token budget.", name, per_example_budget)

        token_count = _estimate_tokens(text)

        # Enforce total budget.
        if running_tokens + token_count > total_budget:
            remaining = total_budget - running_tokens
            if remaining <= 0:
                logger.debug("Total fewshot budget exhausted, stopping.")
                break
            text, _ = _truncate_to_budget(text, remaining)
            token_count = _estimate_tokens(text)

        examples.append(
            FewShotExample(
                source_path=cf.source_path,
                content=text,
                section_slice=section_slice,
                token_count=token_count,
            )
        )
        running_tokens += token_count

    return examples


# ---------------------------------------------------------------------------
# Suggestion helper
# ---------------------------------------------------------------------------


def suggest_examples(
    corpus: Corpus,
    instruction: str,
    *,
    max_suggestions: int = 5,
) -> list[str]:
    """Suggest corpus filenames that may be relevant to *instruction*.

    Relevance is determined by simple keyword overlap between the
    instruction and each file's normalized content.  This function
    **never** auto-selects files; it returns names only so the user can
    make the final choice (SPEC R04).

    Args:
        corpus: A loaded :class:`~writing.corpus.Corpus`.
        instruction: The user's writing instruction or topic description.
        max_suggestions: Maximum number of filenames to return.

    Returns:
        A list of filenames (e.g. ``["intro.md", "methods.tex"]``)
        sorted by descending relevance.
    """
    # Tokenize the instruction into lowercase keywords (3+ chars).
    keywords = {w.lower() for w in re.findall(r"[a-zA-Z]{3,}", instruction)}
    if not keywords:
        return []

    scored: list[tuple[str, int]] = []
    for cf in corpus:
        content_lower = cf.normalized_content.lower()
        hits = sum(1 for kw in keywords if kw in content_lower)
        if hits > 0:
            scored.append((cf.source_path.name, hits))

    # Sort by hit count descending, then alphabetically for stability.
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return [name for name, _score in scored[:max_suggestions]]
