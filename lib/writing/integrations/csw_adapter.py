"""Claude Scientific Writer (CSW) integration adapter.

Implements CSW-style iterative revision and bibliography management patterns
as structured LLM prompts.  This module does **not** depend on any external
CSW package -- it extracts the methodology (multi-round revision, focus-area
checklists, citation consistency) and encodes it directly into prompts
dispatched via the :class:`~writing.backends.LLMBackend` abstraction.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from writing.backends import get_backend

if TYPE_CHECKING:
    from writing.backends import LLMBackend
    from writing.bibliography import Bibliography
    from writing.models import StyleProfile

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class CSWRevisionConfig(BaseModel):
    """Tuning knobs for the CSW-style iterative revision loop.

    Attributes:
        max_revision_rounds: Upper bound on the number of revision passes.
        focus_areas: Quality dimensions the revision prompt will emphasise.
    """

    max_revision_rounds: int = 3
    focus_areas: list[str] = Field(
        default_factory=lambda: [
            "clarity",
            "coherence",
            "citation_accuracy",
            "argument_structure",
        ],
    )


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class CSWAdapter:
    """Applies Claude Scientific Writer revision patterns via LLM prompts.

    The adapter wraps an :class:`~writing.backends.LLMBackend` and provides
    two main capabilities:

    1. **Iterative revision** -- sending academic text through one or more
       rounds of structured revision prompts that target clarity, coherence,
       citation accuracy, and argument structure.
    2. **Bibliography reference management** -- prompting the LLM to align
       in-text citations with a canonical :class:`~writing.bibliography.Bibliography`.
    """

    def __init__(
        self,
        backend: LLMBackend | None = None,
        config: CSWRevisionConfig | None = None,
    ) -> None:
        """Initialise the adapter with an LLM backend and revision config.

        Args:
            backend: LLM backend to use for generation.  Falls back to
                :func:`~writing.backends.get_backend` when ``None``.
            config: Revision loop configuration.  Uses defaults when ``None``.
        """
        self._backend: LLMBackend = backend or get_backend()
        self._config: CSWRevisionConfig = config or CSWRevisionConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def iterative_revise(
        self,
        text: str,
        *,
        style_profile: StyleProfile | None = None,
        bibliography: Bibliography | None = None,
        feedback: str = "",
    ) -> str:
        """Perform a single CSW-style revision pass on *text*.

        Constructs a revision prompt that targets the configured focus areas
        and sends it through the LLM backend.

        Args:
            text: The academic text to revise.
            style_profile: Optional style constraints to preserve during
                revision.
            bibliography: Optional bibliography for citation-aware revision.
            feedback: Optional free-form reviewer feedback to incorporate.

        Returns:
            The revised text returned by the LLM.
        """
        prompt = self._build_revision_prompt(text, style_profile, bibliography, feedback)
        system = (
            "You are an expert academic writing editor following the Claude "
            "Scientific Writer methodology. Return ONLY the revised text, "
            "with no preamble or explanation."
        )
        return self._backend.generate(prompt, system=system)

    def revision_loop(
        self,
        text: str,
        *,
        style_profile: StyleProfile | None = None,
        bibliography: Bibliography | None = None,
        max_rounds: int | None = None,
    ) -> list[str]:
        """Run multiple revision passes, stopping early when changes are minimal.

        Each round calls :meth:`iterative_revise`.  The loop terminates when
        either *max_rounds* is reached or the latest revision differs from
        the previous version by less than 5 % of characters.

        Args:
            text: The starting academic text.
            style_profile: Optional style constraints.
            bibliography: Optional bibliography for citation-aware revision.
            max_rounds: Override for
                :attr:`CSWRevisionConfig.max_revision_rounds`.

        Returns:
            A list of all text versions produced, starting with the original
            and including each successive revision.
        """
        rounds = max_rounds if max_rounds is not None else self._config.max_revision_rounds
        versions: list[str] = [text]

        for round_idx in range(rounds):
            revised = self.iterative_revise(
                versions[-1],
                style_profile=style_profile,
                bibliography=bibliography,
            )
            versions.append(revised)

            if self._is_minimal_change(versions[-2], revised):
                logger.info(
                    "Revision loop converged after %d round(s) (minimal change).",
                    round_idx + 1,
                )
                break

        return versions

    def manage_bibliography_references(
        self,
        text: str,
        bibliography: Bibliography,
    ) -> str:
        """Normalise in-text citations to match the bibliography.

        Sends a prompt asking the LLM to ensure every citation in *text*
        uses consistent formatting and corresponds to a real entry in
        *bibliography*.

        Args:
            text: Academic text containing citations.
            bibliography: The canonical bibliography to reconcile against.

        Returns:
            The text with citation references cleaned up.
        """
        bib_block = _format_bibliography_block(bibliography)
        prompt = (
            "Below is an academic text followed by the authoritative bibliography.\n"
            "Your task:\n"
            "1. Ensure every in-text citation (e.g. [Author, Year] or "
            "\\cite{key}) matches a bibliography entry.\n"
            "2. Standardise citation formatting throughout the text.\n"
            "3. Flag or remove citations that have no matching bibliography entry.\n"
            "4. Do NOT alter the substantive content -- only adjust citations.\n\n"
            "--- TEXT ---\n"
            f"{text}\n\n"
            "--- BIBLIOGRAPHY ---\n"
            f"{bib_block}\n\n"
            "Return ONLY the revised text with corrected citations."
        )
        system = (
            "You are a meticulous academic reference manager. "
            "Return ONLY the revised text, with no preamble or explanation."
        )
        return self._backend.generate(prompt, system=system)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_revision_prompt(
        self,
        text: str,
        style_profile: StyleProfile | None,
        bibliography: Bibliography | None,
        feedback: str,
    ) -> str:
        """Construct the full revision prompt sent to the LLM.

        The prompt instructs the model to revise *text* with attention to
        each configured focus area, optionally incorporating a style
        profile, bibliography context, and reviewer feedback.

        Args:
            text: The text to revise.
            style_profile: Optional writing-style constraints.
            bibliography: Optional bibliography for citation context.
            feedback: Optional reviewer feedback.

        Returns:
            The assembled prompt string.
        """
        focus_list = ", ".join(self._config.focus_areas)
        parts: list[str] = [
            "Revise the following academic text with particular attention to: "
            f"{focus_list}.\n",
        ]

        if style_profile is not None:
            parts.append(
                "Maintain the author's writing style as described below:\n"
                f"  Tone: {style_profile.tone}\n"
                f"  Vocabulary level: {style_profile.vocabulary_level}\n"
                f"  Sentence patterns: {', '.join(style_profile.sentence_patterns)}\n"
                f"  Paragraph structure: {style_profile.paragraph_structure}\n",
            )

        if bibliography is not None:
            bib_block = _format_bibliography_block(bibliography)
            parts.append(
                "Ensure citations are consistent with the following bibliography:\n"
                f"{bib_block}\n",
            )

        if feedback:
            parts.append(f"Incorporate the following reviewer feedback:\n{feedback}\n")

        parts.append(f"--- TEXT ---\n{text}")

        return "\n".join(parts)

    @staticmethod
    def _is_minimal_change(old: str, new: str, threshold: float = 0.05) -> bool:
        """Check whether the revision changed less than *threshold* of the text.

        Uses character-level difference relative to the length of the longer
        string to decide convergence.

        Args:
            old: Previous version of the text.
            new: Revised version of the text.
            threshold: Maximum fractional difference to consider "minimal".

        Returns:
            ``True`` when the change is below *threshold*.
        """
        max_len = max(len(old), len(new))
        if max_len == 0:
            return True
        diff = abs(len(new) - len(old))
        return diff / max_len < threshold


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _format_bibliography_block(bibliography: Bibliography) -> str:
    """Render a bibliography as a plain-text block suitable for prompt injection.

    Args:
        bibliography: The bibliography to render.

    Returns:
        A newline-separated string of formatted citation entries.
    """
    lines = [
        f'[{entry.key}] {entry.authors} ({entry.year}). "{entry.title}".'
        for entry in bibliography
    ]
    return "\n".join(lines)
