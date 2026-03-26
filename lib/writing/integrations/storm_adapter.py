"""Adapter for Stanford's STORM (knowledge_storm) outline generation.

STORM is an optional dependency (``pip install ai-writer[all]``).  This
module uses lazy imports so the rest of the codebase can reference the
adapter without requiring the package to be installed.
"""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    import types

logger = logging.getLogger(__name__)


class StormAdapter:
    """Thin wrapper around ``knowledge_storm`` for outline generation.

    The adapter lazily imports ``knowledge_storm`` only when methods that
    need it are actually called.  If the package is absent, calling
    STORM-dependent methods raises ``ImportError`` with an actionable
    message.

    Attributes:
        web_search_enabled: Whether STORM should use live web search
            during outline synthesis.
    """

    _INSTALL_HINT: ClassVar[str] = (
        "knowledge_storm is not installed. "
        "Install it with:  pip install ai-writer[all]"
    )

    def __init__(self, *, web_search_enabled: bool = True) -> None:
        """Store configuration for later use.

        Args:
            web_search_enabled: If ``True``, STORM will attempt live web
                searches when generating outlines.
        """
        self.web_search_enabled: bool = web_search_enabled

    # ------------------------------------------------------------------
    # Availability check
    # ------------------------------------------------------------------

    @classmethod
    def is_available(cls) -> bool:
        """Check whether ``knowledge_storm`` can be imported.

        Returns:
            ``True`` when the package is importable, ``False`` otherwise.
        """
        try:
            importlib.import_module("knowledge_storm")
        except ImportError:
            return False
        return True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_outline(
        self,
        topic: str,
        corpus_context: str = "",
        *,
        num_perspectives: int = 3,
    ) -> list[str]:
        """Use STORM to generate a document outline for *topic*.

        Args:
            topic: The subject to outline.
            corpus_context: Optional reference text to ground the outline
                in the user's writing corpus.
            num_perspectives: Number of research perspectives STORM
                should consider when building the outline.

        Returns:
            A list of section titles comprising the generated outline.

        Raises:
            ImportError: If ``knowledge_storm`` is not installed.
            RuntimeError: If STORM's internal API call fails unexpectedly.
        """
        storm = self._import_storm()
        prepared_context = self._prepare_corpus_context(corpus_context)

        try:
            runner = storm.STORMWikiRunner  # type: ignore[attr-defined]
            outline_result = runner.generate_outline(  # type: ignore[attr-defined]
                topic=topic,
                context=prepared_context,
                num_perspectives=num_perspectives,
                web_search=self.web_search_enabled,
            )
            # STORM returns outlines in various formats depending on
            # version; normalise to a flat list of section title strings.
            if isinstance(outline_result, list):
                return [str(item) for item in outline_result]
            # Some versions return an object with a `sections` attribute.
            if hasattr(outline_result, "sections"):
                return [
                    str(s.title if hasattr(s, "title") else s)
                    for s in outline_result.sections  # type: ignore[union-attr]
                ]
            return [str(outline_result)]
        except Exception as exc:
            msg = f"STORM outline generation failed for topic '{topic}': {exc}"
            raise RuntimeError(msg) from exc

    @staticmethod
    def generate_outline_simple(
        topic: str,
        sections_hint: list[str],
    ) -> list[str]:
        """Return a basic outline without relying on STORM.

        This fallback simply structures the caller-provided section
        hints into an ordered outline.  No external packages are
        required.

        Args:
            topic: The document topic (used as the first section if
                no hints are provided).
            sections_hint: Suggested section titles.  Returned as-is
                when non-empty.

        Returns:
            A list of section title strings.
        """
        if sections_hint:
            return list(sections_hint)
        return [
            "Introduction",
            f"Background on {topic}",
            "Methodology",
            "Analysis",
            "Discussion",
            "Conclusion",
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prepare_corpus_context(self, corpus_context: str) -> str:
        """Format corpus text for consumption by STORM.

        Strips leading/trailing whitespace and truncates excessively
        long contexts to avoid exceeding STORM's input limits.

        Args:
            corpus_context: Raw corpus text.

        Returns:
            Cleaned context string ready for STORM input.
        """
        max_chars = 50_000
        cleaned = corpus_context.strip()
        if len(cleaned) > max_chars:
            logger.warning(
                "Corpus context truncated from %d to %d characters",
                len(cleaned),
                max_chars,
            )
            cleaned = cleaned[:max_chars]
        return cleaned

    @classmethod
    def _import_storm(cls) -> types.ModuleType:
        """Lazily import ``knowledge_storm``.

        Returns:
            The ``knowledge_storm`` module object.

        Raises:
            ImportError: If the package is not installed.
        """
        try:
            return importlib.import_module("knowledge_storm")
        except ImportError:
            raise ImportError(cls._INSTALL_HINT) from None
