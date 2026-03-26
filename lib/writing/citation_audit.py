"""Citation audit: extract, verify, and report on citations in a document.

Scans text for citation keys in LaTeX, Markdown, and inline formats, then
cross-references them against a :class:`~writing.bibliography.Bibliography`.
Unknown citations are flagged for user review -- never silently removed
(SPEC R07, R16).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from writing.bibliography import Bibliography

# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------


class CitationAuditResult(BaseModel):
    """Outcome of auditing citations found in a document.

    Attributes:
        verified: Citation keys that exist in the bibliography.
        unknown: Citation keys that were NOT found in the bibliography.
        total_citations: Total number of unique citation keys encountered.
    """

    verified: list[str] = Field(default_factory=list)
    unknown: list[str] = Field(default_factory=list)
    total_citations: int = 0


# ---------------------------------------------------------------------------
# Citation-key extraction
# ---------------------------------------------------------------------------

# LaTeX: \cite{key}, \citep{key}, \citet{key}, \cite{k1,k2}
_LATEX_CITE_RE = re.compile(r"\\cite[pt]?\{([^}]+)\}")

# Markdown: [@key] or [@key1; @key2]
_MD_CITE_RE = re.compile(r"\[(@[^]]+)\]")

# Inline: (Author, Year) -- e.g. (Smith, 2020) or (Smith et al., 2020)
_INLINE_CITE_RE = re.compile(
    r"\(([A-Z][A-Za-z]+(?:\s+et\s+al\.)?),\s*(\d{4})\)",
)


def extract_citation_keys(text: str) -> list[str]:
    r"""Extract all citation keys from *text*.

    Supported formats:

    * **LaTeX**: ``\cite{key}``, ``\citep{key}``, ``\citet{key}``,
      ``\cite{key1,key2}``
    * **Markdown**: ``[@key]``, ``[@key1; @key2]``
    * **Inline**: ``(Author, Year)`` patterns (returned as ``Author, Year``
      pseudo-keys for later matching against the bibliography).

    Args:
        text: Document text to scan.

    Returns:
        Deduplicated list of citation keys in the order first encountered.
    """
    seen: set[str] = set()
    keys: list[str] = []

    def _add(key: str) -> None:
        k = key.strip()
        if k and k not in seen:
            seen.add(k)
            keys.append(k)

    # LaTeX citations
    for match in _LATEX_CITE_RE.finditer(text):
        for raw_key in match.group(1).split(","):
            _add(raw_key)

    # Markdown citations
    for match in _MD_CITE_RE.finditer(text):
        for fragment in match.group(1).split(";"):
            clean = fragment.strip().lstrip("@").strip()
            _add(clean)

    # Inline citations -- synthesise a pseudo-key "Author, Year"
    for match in _INLINE_CITE_RE.finditer(text):
        pseudo = f"{match.group(1)}, {match.group(2)}"
        _add(pseudo)

    return keys


# ---------------------------------------------------------------------------
# Audit logic
# ---------------------------------------------------------------------------


def audit_citations(text: str, bibliography: Bibliography) -> CitationAuditResult:
    """Audit all citations in *text* against *bibliography*.

    Each extracted key is classified as *verified* (present in the
    bibliography) or *unknown* (absent).  Unknown citations are flagged
    but **never** auto-removed -- they must be presented to the user for
    decision (SPEC R07, R16).

    Args:
        text: Document text to audit.
        bibliography: The reference bibliography to check against.

    Returns:
        A :class:`CitationAuditResult` summarising the audit.
    """
    keys = extract_citation_keys(text)

    verified: list[str] = []
    unknown: list[str] = []

    for key in keys:
        if bibliography.contains(key):
            verified.append(key)
        else:
            # For inline pseudo-keys ("Author, Year"), attempt a fuzzy match
            # against bibliography entries before marking unknown.
            matched = _try_inline_match(key, bibliography)
            if matched:
                verified.append(key)
            else:
                unknown.append(key)

    return CitationAuditResult(
        verified=verified,
        unknown=unknown,
        total_citations=len(keys),
    )


def _try_inline_match(pseudo_key: str, bibliography: Bibliography) -> bool:
    """Attempt to match an inline pseudo-key against bibliography entries.

    Inline pseudo-keys have the form ``"Author, Year"``.  We check whether
    any bibliography entry contains the author surname and matches the year.

    Args:
        pseudo_key: A string like ``"Smith, 2020"`` or ``"Smith et al., 2020"``.
        bibliography: Bibliography to search.

    Returns:
        ``True`` if a plausible match was found.
    """
    parts = pseudo_key.rsplit(",", maxsplit=1)
    if len(parts) != 2:
        return False

    author_fragment = parts[0].replace("et al.", "").strip().lower()
    year_str = parts[1].strip()

    try:
        year = int(year_str)
    except ValueError:
        return False

    for entry in bibliography.entries.values():
        if entry.year == year and author_fragment in entry.authors.lower():
            return True

    return False


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------


def format_audit_report(result: CitationAuditResult, bibliography: Bibliography) -> str:
    """Format a human-readable audit report.

    The report lists verified citations with their titles and flags unknown
    citations for user review.

    Args:
        result: The audit result to format.
        bibliography: Bibliography used for title look-ups.

    Returns:
        Multi-line string suitable for display or logging.
    """
    lines: list[str] = [
        "Citation Audit Report",
        "=" * 40,
        f"Total unique citations: {result.total_citations}",
        f"Verified: {len(result.verified)}",
        f"Unknown:  {len(result.unknown)}",
        "",
    ]

    if result.verified:
        lines.append("Verified Citations")
        lines.append("-" * 40)
        for key in result.verified:
            entry = bibliography.get(key)
            if entry:
                lines.append(f"  [OK] {key} -- {entry.title} ({entry.year})")
            else:
                # Inline pseudo-key matched but has no direct entry object
                lines.append(f"  [OK] {key}")
        lines.append("")

    if result.unknown:
        lines.append("Unknown Citations (require user review)")
        lines.append("-" * 40)
        lines.extend(f"  [??] {key} -- NOT FOUND in bibliography" for key in result.unknown)
        lines.append("")

    return "\n".join(lines)
