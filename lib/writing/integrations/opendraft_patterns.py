"""OpenDraft citation-pattern detection and fuzzy bibliography matching.

Finds informal citation-like patterns in text (e.g. "Smith et al. (2020)")
that may not use standard LaTeX or Markdown citation syntax, and attempts
to match them to existing bibliography entries.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from writing.bibliography import Bibliography
    from writing.models import CitationEntry

# ---------------------------------------------------------------------------
# Patterns for informal / "citation-like" references
# ---------------------------------------------------------------------------

_AUTHOR_YEAR_PAREN_RE = re.compile(
    r"(?P<authors>[A-Z][A-Za-z]+(?:\s+(?:and|&)\s+[A-Z][A-Za-z]+)?"
    r"(?:\s+et\s+al\.)?)"
    r"\s*\((?P<year>\d{4})\)",
)

# "Smith, 2020" inside parentheses -- e.g. "(Smith, 2020)"
_PAREN_AUTHOR_COMMA_YEAR_RE = re.compile(
    r"\((?P<authors>[A-Z][A-Za-z]+(?:\s+(?:and|&)\s+[A-Z][A-Za-z]+)?"
    r"(?:\s+et\s+al\.)?)"
    r",\s*(?P<year>\d{4})\)",
)


class OpenDraftPatterns:
    """Static helper methods for detecting and matching informal citations.

    All methods are static -- no instance state is needed.
    """

    @staticmethod
    def find_citation_like_patterns(text: str) -> list[str]:
        """Find text fragments that resemble citations but lack formal syntax.

        Detects patterns such as:

        * ``Smith (2020)``
        * ``Smith et al. (2020)``
        * ``Smith and Jones (2020)``
        * ``(Smith, 2020)``

        Args:
            text: Document text to scan.

        Returns:
            Deduplicated list of matched patterns in encounter order.
        """
        seen: set[str] = set()
        patterns: list[str] = []

        for regex in (_AUTHOR_YEAR_PAREN_RE, _PAREN_AUTHOR_COMMA_YEAR_RE):
            for match in regex.finditer(text):
                fragment = match.group(0)
                if fragment not in seen:
                    seen.add(fragment)
                    patterns.append(fragment)

        return patterns

    @staticmethod
    def cross_reference_bibliography(
        patterns: list[str],
        bibliography: Bibliography,
    ) -> dict[str, CitationEntry | None]:
        """Match informal citation patterns against bibliography entries.

        For each pattern, extracts the author surname(s) and year, then
        performs a case-insensitive substring match on
        :attr:`CitationEntry.authors` combined with an exact year match.

        Args:
            patterns: Informal citation strings (e.g. ``"Smith et al. (2020)"``).
            bibliography: Bibliography to search.

        Returns:
            Mapping from each input pattern to the best-matching
            :class:`CitationEntry`, or ``None`` if no match was found.
        """
        results: dict[str, CitationEntry | None] = {}

        for pattern in patterns:
            author_str, year = _parse_author_year(pattern)
            if year is None:
                results[pattern] = None
                continue

            best = _find_best_match(author_str, year, bibliography)
            results[pattern] = best

        return results

    @staticmethod
    def suggest_citation_key(
        pattern: str,
        bibliography: Bibliography,
    ) -> str | None:
        """Suggest a bibliography key for an informal citation pattern.

        Args:
            pattern: An informal citation string (e.g. ``"Smith et al. (2020)"``).
            bibliography: Bibliography to search.

        Returns:
            The most likely citation key, or ``None`` if no match is found.
        """
        author_str, year = _parse_author_year(pattern)
        if year is None:
            return None

        entry = _find_best_match(author_str, year, bibliography)
        return entry.key if entry is not None else None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_author_year(pattern: str) -> tuple[str, int | None]:
    """Extract author fragment and year from an informal citation string.

    Args:
        pattern: A citation-like string.

    Returns:
        Tuple of ``(author_fragment_lower, year)`` or ``(author_fragment_lower, None)``
        if parsing fails.
    """
    # Try both regex styles
    for regex in (_AUTHOR_YEAR_PAREN_RE, _PAREN_AUTHOR_COMMA_YEAR_RE):
        match = regex.search(pattern)
        if match:
            author_str = match.group("authors").strip().lower()
            # Remove "et al." for matching purposes
            author_str = author_str.replace("et al.", "").strip()
            try:
                year = int(match.group("year"))
            except ValueError:
                continue
            return author_str, year

    return pattern.lower(), None


def _find_best_match(
    author_fragment: str,
    year: int,
    bibliography: Bibliography,
) -> CitationEntry | None:
    """Find the bibliography entry best matching an author fragment and year.

    Uses case-insensitive substring matching on the author field plus an
    exact year match.  When multiple entries match, the one whose author
    string is shortest (most specific match) is preferred.

    Args:
        author_fragment: Lowercased author surname(s).
        year: Publication year.
        bibliography: Bibliography to search.

    Returns:
        The best-matching :class:`CitationEntry`, or ``None``.
    """
    # Split on "and" / "&" to get individual surname fragments
    surnames = re.split(r"\s+(?:and|&)\s+", author_fragment)
    candidates: list[CitationEntry] = []

    for entry in bibliography.entries.values():
        if entry.year != year:
            continue

        entry_authors_lower = entry.authors.lower()
        if all(surname.strip() in entry_authors_lower for surname in surnames):
            candidates.append(entry)

    if not candidates:
        return None

    # Prefer the shortest author string (most specific match)
    return min(candidates, key=lambda e: len(e.authors))
