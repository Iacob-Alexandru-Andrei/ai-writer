"""Corpus ingestion and normalization for the ai-writer system.

Scans a directory for ``.md`` and ``.tex`` files, normalises LaTeX to
Markdown (via ``pandoc`` when available, falling back to regex-based
extraction), and exposes the resulting files in paths that Claude Code
can grep and read.
"""

from __future__ import annotations

import contextlib
import functools
import re
import shutil
import subprocess
from pathlib import Path  # noqa: TC003 - Pydantic needs this at runtime
from typing import TYPE_CHECKING, Literal, Self

from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Iterator


# ---------------------------------------------------------------------------
# Pydantic model
# ---------------------------------------------------------------------------


class CorpusFile(BaseModel):
    """A single file ingested from the corpus directory.

    Attributes:
        source_path: Original filesystem path of the source file.
        content: Raw text content as read from disk.
        format: Detected format of the source file.
        normalized_content: Content converted to Markdown.
        word_count: Number of whitespace-delimited words in the
            normalized content.
    """

    source_path: Path
    content: str
    format: Literal["markdown", "latex"]
    normalized_content: str = ""
    word_count: int = 0


# ---------------------------------------------------------------------------
# LaTeX normalization helpers
# ---------------------------------------------------------------------------

_PANDOC_AVAILABLE: bool | None = None


def _check_pandoc_available() -> bool:
    """Return whether the ``pandoc`` binary is on ``$PATH``.

    The result is cached after the first call so subsequent invocations
    are free.

    Returns:
        ``True`` when ``pandoc --version`` exits successfully.
    """
    global _PANDOC_AVAILABLE  # noqa: PLW0603
    if _PANDOC_AVAILABLE is not None:
        return _PANDOC_AVAILABLE

    try:
        subprocess.run(
            ["pandoc", "--version"],  # noqa: S607
            capture_output=True,
            check=True,
            timeout=10,
        )
        _PANDOC_AVAILABLE = True
    except (FileNotFoundError, subprocess.SubprocessError):
        _PANDOC_AVAILABLE = False
    return _PANDOC_AVAILABLE


def _normalize_latex_regex(text: str) -> str:
    r"""Best-effort LaTeX-to-Markdown conversion using regular expressions.

    Handles common patterns such as ``\section{}``, ``\textbf{}``, and
    environment wrappers.  The result is *not* perfect but is sufficient
    for style analysis and substring search.

    Args:
        text: Raw LaTeX source.

    Returns:
        Approximate Markdown rendering of *text*.
    """
    out = text

    # Convert sectioning commands to Markdown headings.
    out = re.sub(r"\\section\*?\{([^}]*)\}", r"## \1", out)
    out = re.sub(r"\\subsection\*?\{([^}]*)\}", r"### \1", out)
    out = re.sub(r"\\subsubsection\*?\{([^}]*)\}", r"#### \1", out)
    out = re.sub(r"\\chapter\*?\{([^}]*)\}", r"# \1", out)
    out = re.sub(r"\\title\{([^}]*)\}", r"# \1", out)

    # Inline formatting.
    out = re.sub(r"\\textbf\{([^}]*)\}", r"**\1**", out)
    out = re.sub(r"\\textit\{([^}]*)\}", r"*\1*", out)
    out = re.sub(r"\\emph\{([^}]*)\}", r"*\1*", out)
    out = re.sub(r"\\underline\{([^}]*)\}", r"\1", out)
    out = re.sub(r"\\texttt\{([^}]*)\}", r"`\1`", out)

    # Strip environment begin/end wrappers (keep inner text).
    out = re.sub(r"\\begin\{[^}]*\}", "", out)
    out = re.sub(r"\\end\{[^}]*\}", "", out)

    # Remove remaining backslash-commands with a single braced argument,
    # keeping the argument text.  This deliberately does NOT match commands
    # that take zero arguments (handled below).
    out = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", out)

    # Remove zero-argument commands like \maketitle, \newpage, etc.
    out = re.sub(r"\\[a-zA-Z]+", "", out)

    # Collapse excessive blank lines.
    out = re.sub(r"\n{3,}", "\n\n", out)

    return out.strip()


def normalize_latex(text: str) -> str:
    """Convert LaTeX source to Markdown.

    Tries ``pandoc`` first (subprocess, stdin/stdout, tex to markdown).
    Falls back to a regex-based extraction when ``pandoc`` is not
    available or fails.

    Args:
        text: Raw LaTeX source text.

    Returns:
        Markdown representation of the input.
    """
    if _check_pandoc_available():
        try:
            result = subprocess.run(
                ["pandoc", "-f", "latex", "-t", "markdown", "--wrap=none"],  # noqa: S607
                input=text,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            return result.stdout.strip()
        except subprocess.SubprocessError:
            pass  # fall through to regex path

    return _normalize_latex_regex(text)


# ---------------------------------------------------------------------------
# Corpus class
# ---------------------------------------------------------------------------

_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".md", ".tex"})


class Corpus:
    """Managed collection of ``.md`` and ``.tex`` files from a directory.

    Typical usage::

        corpus = Corpus(Path("./papers")).load()
        for f in corpus:
            print(f.source_path.name, f.word_count)

    Attributes:
        directory: Root directory that was scanned.
    """

    def __init__(self, directory: Path) -> None:
        """Initialise the corpus for *directory* (does **not** load yet).

        Args:
            directory: Path to the directory containing source files.
        """
        self.directory: Path = directory
        self._files: list[CorpusFile] = []

    # -- loading -----------------------------------------------------------

    def load(self) -> Self:
        """Scan the directory and ingest all ``.md`` / ``.tex`` files.

        Returns:
            ``self`` so calls can be chained (e.g. ``Corpus(d).load()``).

        Raises:
            FileNotFoundError: If *directory* does not exist.
        """
        if not self.directory.exists():
            msg = f"Corpus directory does not exist: {self.directory}"
            raise FileNotFoundError(msg)

        self._files = []
        for path in sorted(self.directory.rglob("*")):
            if path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
                continue
            if not path.is_file():
                continue

            raw = path.read_text(encoding="utf-8", errors="replace")
            fmt: Literal["markdown", "latex"] = (
                "latex" if path.suffix.lower() == ".tex" else "markdown"
            )
            normalized = normalize_latex(raw) if fmt == "latex" else raw
            word_count = len(normalized.split())

            self._files.append(
                CorpusFile(
                    source_path=path,
                    content=raw,
                    format=fmt,
                    normalized_content=normalized,
                    word_count=word_count,
                )
            )

        return self

    # -- accessors ---------------------------------------------------------

    @property
    def files(self) -> list[CorpusFile]:
        """Return all loaded corpus files.

        Returns:
            A list of ``CorpusFile`` instances.
        """
        return list(self._files)

    def get_file(self, name: str) -> CorpusFile | None:
        """Look up a corpus file by its filename (stem + extension).

        Args:
            name: Filename to match (e.g. ``"intro.md"``).

        Returns:
            The matching ``CorpusFile``, or ``None`` if not found.
        """
        for f in self._files:
            if f.source_path.name == name:
                return f
        return None

    def search(self, query: str) -> list[CorpusFile]:
        """Return files whose normalized content contains *query*.

        The comparison is case-insensitive.

        Args:
            query: Substring to search for.

        Returns:
            List of matching ``CorpusFile`` instances.
        """
        lower_query = query.lower()
        return [f for f in self._files if lower_query in f.normalized_content.lower()]

    def expose_for_grep(self, target_dir: Path) -> Path:
        """Copy normalized Markdown files into *target_dir*.

        Each file is written as ``<original_stem>.md`` so that
        Claude Code's Grep and Read tools can access the content
        without needing to understand LaTeX.

        Args:
            target_dir: Destination directory (created if absent).

        Returns:
            The *target_dir* path.
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        for f in self._files:
            dest = target_dir / f"{f.source_path.stem}.md"
            dest.write_text(f.normalized_content, encoding="utf-8")
            # Preserve metadata from the original file where possible.
            with contextlib.suppress(OSError):
                shutil.copystat(f.source_path, dest)
        return target_dir

    @functools.cached_property
    def total_words(self) -> int:
        """Return the aggregate word count across all files.

        Returns:
            Total number of words.
        """
        return sum(f.word_count for f in self._files)

    # -- dunder protocols --------------------------------------------------

    def __len__(self) -> int:
        """Return the number of loaded files."""
        return len(self._files)

    def __iter__(self) -> Iterator[CorpusFile]:
        """Iterate over loaded ``CorpusFile`` instances."""
        return iter(self._files)
