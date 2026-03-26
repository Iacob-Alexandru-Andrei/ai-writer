"""Long-form document workflow for paper, thesis, and blog content types.

Implements an interactive outline-then-section workflow per SPEC R06:
style analysis, outline generation, section-by-section generation with
running context, and final assembly with optional citation audit.

Each public method returns control to the caller (slash command) rather
than running a blocking loop -- the user approves each stage before
advancing.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from writing.backends import get_backend
from writing.bibliography import Bibliography
from writing.citation_audit import audit_citations
from writing.corpus import Corpus
from writing.fewshot import select_examples
from writing.integrations.storm_adapter import StormAdapter
from writing.models import (
    ContentType,
    GenerationResult,
    SessionState,
    SessionStatus,
)
from writing.prompt_assembler import assemble_prompt
from writing.session import SessionManager
from writing.settings import WriterSettings, load_settings
from writing.style import analyze_style

if TYPE_CHECKING:
    from pathlib import Path

    from writing.backends import LLMBackend
    from writing.models import FewShotExample

logger = logging.getLogger(__name__)


class LongFormWorkflow:
    """Interactive outline-then-section workflow for long-form documents.

    Designed for ``paper``, ``thesis``, and ``blog`` content types.  Each
    public method corresponds to a single workflow stage and returns
    control to the caller so the user can review output before proceeding.

    Workflow stages (per SPEC R06):
        1. :meth:`start` -- corpus loading and style analysis.
        2. :meth:`generate_outline` -- outline generation (STORM or LLM).
        3. :meth:`generate_section` -- section-by-section generation.
        4. :meth:`finalize` -- citation audit and final document assembly.
    """

    def __init__(
        self,
        *,
        session_manager: SessionManager | None = None,
        backend: LLMBackend | None = None,
        settings: WriterSettings | None = None,
    ) -> None:
        """Initialise the workflow with optional dependency overrides.

        Args:
            session_manager: Session persistence manager.  When *None*,
                a new ``SessionManager`` is created with *settings*.
            backend: LLM backend for text generation.  When *None*,
                ``get_backend()`` selects the default.
            settings: Writer settings.  When *None*, settings are loaded
                via ``load_settings()``.
        """
        self._settings: WriterSettings = settings if settings is not None else load_settings()
        self._session_manager: SessionManager = (
            session_manager if session_manager is not None else SessionManager(self._settings)
        )
        self._backend: LLMBackend = backend if backend is not None else get_backend()
        self._example_files: dict[str, list[str]] = {}

    # ------------------------------------------------------------------
    # Public workflow stages
    # ------------------------------------------------------------------

    def start(
        self,
        *,
        content_type: ContentType,
        instruction: str,
        corpus_dir: Path,
        bibliography_path: Path | None = None,
        example_files: list[str] | None = None,
    ) -> SessionState:
        """Create a session, load corpus, run style analysis, and save the profile.

        This is stage 1 of the workflow.  The returned session has status
        ``ANALYZING`` and a populated ``style_profile``.

        Args:
            content_type: The document type to generate (paper, thesis, blog).
            instruction: User-provided writing instruction or topic.
            corpus_dir: Path to the directory containing reference documents.
            bibliography_path: Optional path to a BibTeX or Markdown
                bibliography file.
            example_files: Optional list of filenames within *corpus_dir*
                to use as few-shot examples.

        Returns:
            A ``SessionState`` in ``ANALYZING`` status with the style
            profile populated.
        """
        session = self._session_manager.create(
            content_type=content_type,
            instruction=instruction,
            corpus_dir=corpus_dir,
            bibliography_path=bibliography_path,
        )
        logger.info("Created session %s for %s", session.session_id, content_type.value)

        # Store example file names for later use during section generation.
        if example_files:
            self._example_files[session.session_id] = list(example_files)

        # Load corpus and run style analysis.
        corpus = self._load_corpus(session)
        profile = analyze_style(corpus, self._backend)
        self._session_manager.set_style_profile(session, profile)
        self._session_manager.set_status(session, SessionStatus.ANALYZING)

        logger.info("Style analysis complete for session %s", session.session_id)
        return session

    def generate_outline(self, session: SessionState) -> list[str]:
        """Generate a document outline for the session.

        Uses the STORM adapter when available; otherwise prompts the LLM
        directly.  Updates the session with the outline and sets status
        to ``OUTLINING``.

        Args:
            session: An active session (typically in ``ANALYZING`` status).

        Returns:
            Ordered list of section titles comprising the outline.
        """
        corpus = self._load_corpus(session)
        corpus_context = "\n\n".join(cf.normalized_content for cf in corpus.files)

        if StormAdapter.is_available():
            logger.info("Using STORM adapter for outline generation")
            adapter = StormAdapter(web_search_enabled=False)
            try:
                outline = adapter.generate_outline(
                    topic=session.instruction,
                    corpus_context=corpus_context,
                )
            except (ImportError, RuntimeError):
                logger.warning("STORM outline failed, falling back to LLM")
                outline = self._generate_outline_via_llm(session, corpus_context)
        else:
            logger.info("STORM not available, generating outline via LLM")
            outline = self._generate_outline_via_llm(session, corpus_context)

        self._session_manager.set_outline(session, outline)
        self._session_manager.set_status(session, SessionStatus.OUTLINING)

        logger.info(
            "Outline generated for session %s: %d sections",
            session.session_id,
            len(outline),
        )
        return outline

    def generate_section(self, session: SessionState) -> GenerationResult:
        """Generate the next section using the prompt assembler.

        Builds running context from previously generated sections,
        assembles a prompt, calls the LLM backend, and advances the
        session.  Sets status to ``GENERATING``.

        Args:
            session: An active session with an outline and at least one
                remaining section to generate.

        Returns:
            A ``GenerationResult`` for the newly generated section.

        Raises:
            IndexError: If all outline sections have already been generated.
        """
        if session.current_section_index >= len(session.outline):
            msg = (
                f"All {len(session.outline)} sections already generated "
                f"for session {session.session_id}"
            )
            raise IndexError(msg)

        section_name = session.outline[session.current_section_index]
        running_context = self._build_running_context(session)

        # Load optional resources.
        corpus = self._load_corpus(session)
        bibliography = self._load_bibliography(session)
        examples = self._select_examples(session, corpus)

        prompt = assemble_prompt(
            content_type=session.content_type,
            instruction=session.instruction,
            section_name=section_name,
            style_profile=session.style_profile,
            few_shot_examples=examples,
            running_context=running_context,
            bibliography=bibliography,
            outline=session.outline,
            settings=self._settings,
        )

        content = self._backend.generate(prompt.user_prompt, system=prompt.system_prompt or None)

        result = GenerationResult(
            content=content,
            section_name=section_name,
            token_count=prompt.total_tokens,
        )

        self._session_manager.advance(session, result)
        self._session_manager.set_status(session, SessionStatus.GENERATING)

        logger.info(
            "Generated section '%s' (%d/%d) for session %s",
            section_name,
            session.current_section_index,
            len(session.outline),
            session.session_id,
        )
        return result

    def get_status(self, session: SessionState) -> dict[str, object]:
        """Return a summary of the current workflow state.

        Args:
            session: The session to report on.

        Returns:
            A dict with keys ``total_sections``, ``completed_sections``,
            ``current_section``, ``status``, and ``outline``.
        """
        total = len(session.outline)
        completed = len(session.sections)
        current_section = (
            session.outline[session.current_section_index]
            if session.current_section_index < total
            else None
        )

        return {
            "total_sections": total,
            "completed_sections": completed,
            "current_section": current_section,
            "status": session.status.value,
            "outline": list(session.outline),
        }

    def finalize(self, session: SessionState) -> str:
        """Run citation audit (if applicable) and assemble the final document.

        Sets the session status to ``COMPLETE`` and returns the full
        document text.

        Args:
            session: A session with all sections generated.

        Returns:
            The assembled document text with section headers.
        """
        document = self._assemble_final_document(session)

        # Run citation audit if a bibliography is available.
        bibliography = self._load_bibliography(session)
        if bibliography is not None:
            audit_result = audit_citations(document, bibliography)
            if audit_result.unknown:
                logger.warning(
                    "Citation audit found %d unknown citations: %s",
                    len(audit_result.unknown),
                    ", ".join(audit_result.unknown),
                )

        self._session_manager.set_status(session, SessionStatus.COMPLETE)
        self._session_manager.save(session)

        logger.info("Session %s finalized", session.session_id)
        return document

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_corpus(self, session: SessionState) -> Corpus:
        """Load and return a ``Corpus`` from the session's corpus directory.

        Args:
            session: The active session.

        Returns:
            A loaded ``Corpus`` instance.

        Raises:
            FileNotFoundError: If the corpus directory is not set or missing.
        """
        if session.corpus_dir is None:
            msg = f"No corpus directory set for session {session.session_id}"
            raise FileNotFoundError(msg)
        return Corpus(session.corpus_dir).load()

    def _load_bibliography(self, session: SessionState) -> Bibliography | None:
        """Load the bibliography if a path is set on the session.

        Args:
            session: The active session.

        Returns:
            A loaded ``Bibliography``, or ``None`` if no path is configured.
        """
        if session.bibliography_path is None:
            return None
        return Bibliography().load(session.bibliography_path)

    def _build_running_context(self, session: SessionState) -> str:
        """Build running context from previously generated sections.

        Summarises key arguments, terms, and examples used in prior
        sections to maintain coherence across the document.

        Args:
            session: The active session with accumulated sections.

        Returns:
            A formatted context string, or an empty string if no
            sections have been generated yet.
        """
        if not session.sections:
            return ""

        parts: list[str] = [
            "Previously generated sections (summary for continuity):",
            "",
        ]
        for section in session.sections:
            # Include section name and a truncated preview of the content.
            preview_words = section.content.split()[:150]
            preview = " ".join(preview_words)
            if len(section.content.split()) > 150:
                preview += " [...]"
            parts.append(f"### {section.section_name}")
            parts.append(preview)
            parts.append("")

        return "\n".join(parts)

    def _assemble_final_document(self, session: SessionState) -> str:
        """Join all generated section contents with Markdown headers.

        Args:
            session: The session containing completed sections.

        Returns:
            A single string containing the full document.
        """
        parts: list[str] = []
        for section in session.sections:
            parts.append(f"## {section.section_name}")
            parts.append("")
            parts.append(section.content)
            parts.append("")

        return "\n".join(parts).rstrip() + "\n"

    def _generate_outline_via_llm(
        self,
        session: SessionState,
        corpus_context: str,
    ) -> list[str]:
        """Generate an outline by prompting the LLM directly.

        Used as a fallback when STORM is not available.

        Args:
            session: The active session.
            corpus_context: Concatenated corpus text for grounding.

        Returns:
            A list of section title strings.
        """
        prompt = (
            f"Generate a document outline for a {session.content_type.value} "
            f"on the following topic:\n\n"
            f"{session.instruction}\n\n"
            f"Context from reference documents:\n{corpus_context[:5000]}\n\n"
            f"Return ONLY a numbered list of section titles, one per line. "
            f"Do not include any other text."
        )
        response = self._backend.generate(prompt)
        return self._parse_outline_response(response)

    @staticmethod
    def _parse_outline_response(response: str) -> list[str]:
        """Parse an LLM response into a list of section titles.

        Handles numbered lists (``1. Title``), bulleted lists (``- Title``),
        and plain lines.

        Args:
            response: Raw LLM response text.

        Returns:
            A list of cleaned section title strings.
        """
        lines = response.strip().splitlines()
        sections: list[str] = []
        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue
            # Strip numbering patterns like "1.", "1)", "1:"
            cleaned = re.sub(r"^\d+[.):\-]\s*", "", cleaned)
            # Strip bullet markers.
            cleaned = re.sub(r"^[-*+]\s*", "", cleaned)
            cleaned = cleaned.strip()
            if cleaned:
                sections.append(cleaned)
        return sections

    def _select_examples(
        self,
        session: SessionState,
        corpus: Corpus,
    ) -> list[FewShotExample]:
        """Select few-shot examples from the corpus for the current session.

        Uses explicitly provided example files if they were passed to
        :meth:`start`; otherwise falls back to the first few corpus files.

        Args:
            session: The active session (used to look up stored example files).
            corpus: The loaded corpus.

        Returns:
            A list of few-shot examples. Empty if no corpus files are available.
        """
        if not corpus.files:
            return []
        # Prefer explicitly provided example files from start().
        stored = self._example_files.get(session.session_id)
        if stored:
            file_names = stored
        else:
            max_ex = self._settings.max_fewshot_examples
            file_names = [
                cf.source_path.name for cf in corpus.files[:max_ex]
            ]
        return select_examples(corpus, file_names, settings=self._settings)
