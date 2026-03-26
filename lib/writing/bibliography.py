"""Bibliography loader: parses BibTeX and structured-markdown citation files.

Provides the :class:`Bibliography` class that normalises citations from ``.bib``
and ``.md`` files into a uniform :class:`~writing.models.CitationEntry` store.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import bibtexparser

from writing.models import CitationEntry

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from bibtexparser.bibdatabase import BibDatabase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Markdown bibliography regex
# ---------------------------------------------------------------------------
# Matches lines like:
#   - **key**: Author (Year). "Title". *Source*.
# Also accepts single-quoted titles and missing source.
_MD_ENTRY_RE = re.compile(
    r"""
    ^-\s+\*\*(?P<key>[^*]+)\*\*           # - **cite_key**
    :\s*                                   # colon separator
    (?P<authors>.+?)                       # author(s) — greedy-minimal
    \s*\((?P<year>\d{4})\)                 # (Year)
    \.\s*                                  # period
    [""\u201c](?P<title>.+?)[""\u201d]     # "Title" (straight or curly quotes)
    (?:\.\s*\*(?P<source>[^*]+)\*)?        # optional *Source*
    """,
    re.VERBOSE,
)


class Bibliography:
    """Normalised citation database loaded from BibTeX or Markdown files.

    Example::

        bib = Bibliography().load(Path("refs.bib"))
        if "vaswani2017" in bib:
            entry = bib.get("vaswani2017")
    """

    def __init__(self) -> None:
        """Initialise an empty bibliography."""
        self._entries: dict[str, CitationEntry] = {}

    # -- public properties ---------------------------------------------------

    @property
    def entries(self) -> dict[str, CitationEntry]:
        """Return the full mapping of citation key to entry."""
        return self._entries

    @property
    def keys(self) -> list[str]:
        """Return all citation keys as a list."""
        return list(self._entries.keys())

    # -- loaders -------------------------------------------------------------

    def load_bibtex(self, path: Path) -> Bibliography:
        """Parse a ``.bib`` file and add entries to the bibliography.

        Args:
            path: Filesystem path to the BibTeX file.

        Returns:
            ``self`` for method chaining.
        """
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return self

        parser = bibtexparser.bparser.BibTexParser(common_strings=True)
        db: BibDatabase = bibtexparser.loads(text, parser=parser)

        for raw in db.entries:
            try:
                entry = _bibtex_record_to_entry(raw)
            except Exception:
                logger.warning("Skipping malformed BibTeX entry: %s", raw.get("ID", "<unknown>"))
                continue
            self._entries[entry.key] = entry

        return self

    def load_markdown(self, path: Path) -> Bibliography:
        """Parse a structured-markdown bibliography file.

        Expected line format::

            - **key**: Author (Year). "Title". *Source*.

        Lines that do not match are silently skipped.

        Args:
            path: Filesystem path to the Markdown file.

        Returns:
            ``self`` for method chaining.
        """
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            match = _MD_ENTRY_RE.match(line.strip())
            if match is None:
                continue
            entry = _md_match_to_entry(match)
            self._entries[entry.key] = entry

        return self

    def load(self, path: Path) -> Bibliography:
        """Auto-detect file format by extension and delegate to the right loader.

        Args:
            path: Filesystem path (``.bib`` or ``.md``).

        Returns:
            ``self`` for method chaining.

        Raises:
            ValueError: If the file extension is not recognised.
        """
        suffix = path.suffix.lower()
        if suffix == ".bib":
            return self.load_bibtex(path)
        if suffix == ".md":
            return self.load_markdown(path)
        msg = f"Unsupported bibliography format: {suffix}"
        raise ValueError(msg)

    # -- lookup helpers ------------------------------------------------------

    def get(self, key: str) -> CitationEntry | None:
        """Look up a citation by key, returning ``None`` if absent.

        Args:
            key: The citation key to search for.

        Returns:
            The matching :class:`CitationEntry` or ``None``.
        """
        return self._entries.get(key)

    def contains(self, key: str) -> bool:
        """Check whether *key* exists in the bibliography.

        Args:
            key: Citation key.

        Returns:
            ``True`` if the key is present.
        """
        return key in self._entries

    # -- dunder protocols ----------------------------------------------------

    def __len__(self) -> int:
        """Return the number of entries."""
        return len(self._entries)

    def __iter__(self) -> Iterator[CitationEntry]:
        """Iterate over all :class:`CitationEntry` instances."""
        return iter(self._entries.values())

    def __contains__(self, key: object) -> bool:
        """Support ``"key" in bibliography`` syntax."""
        if not isinstance(key, str):
            return False
        return key in self._entries


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _bibtex_record_to_entry(raw: dict[str, str]) -> CitationEntry:
    """Convert a raw bibtexparser dict to a :class:`CitationEntry`.

    Args:
        raw: Dictionary produced by ``bibtexparser`` for a single entry.

    Returns:
        A validated :class:`CitationEntry`.
    """
    key = raw.get("ID", "")
    title = raw.get("title", key) or key
    authors = raw.get("author", "")
    source_type = raw.get("ENTRYTYPE", "")

    year_raw = raw.get("year", "0")
    try:
        year = int(year_raw)
    except (ValueError, TypeError):
        year = 0

    return CitationEntry(
        key=key,
        title=title,
        authors=authors,
        year=year,
        source_type=source_type,
    )


def _md_match_to_entry(match: re.Match[str]) -> CitationEntry:
    """Convert a regex match from a markdown bibliography line to a :class:`CitationEntry`.

    Args:
        match: A successful match of :data:`_MD_ENTRY_RE`.

    Returns:
        A validated :class:`CitationEntry`.
    """
    key = match.group("key").strip()
    authors = match.group("authors").strip()
    title = match.group("title").strip()
    source = (match.group("source") or "").strip()

    year_str = match.group("year")
    try:
        year = int(year_str)
    except (ValueError, TypeError):
        year = 0

    return CitationEntry(
        key=key,
        title=title or key,
        authors=authors,
        year=year,
        source_type=source,
    )
