"""Short-form content workflow for LinkedIn and Twitter/X.

Implements a single-generation + review cycle without an outline step.
The workflow is non-blocking: each method returns control to the caller
so the user can inspect results, provide feedback, or finalize between
calls.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from writing.backends import get_backend
from writing.models import ContentType, GenerationResult, SessionStatus
from writing.prompt_assembler import AssembledPrompt, assemble_prompt
from writing.session import SessionManager
from writing.settings import load_settings
from writing.validators import validate_content

if TYPE_CHECKING:
    from pathlib import Path

    from writing.backends import LLMBackend
    from writing.models import SessionState, StyleProfile
    from writing.settings import WriterSettings

logger = logging.getLogger(__name__)

_SHORT_FORM_TYPES: frozenset[ContentType] = frozenset(
    {ContentType.LINKEDIN, ContentType.TWITTER},
)
"""Content types handled by the short-form workflow."""


class ShortFormWorkflow:
    """Single-generation + review workflow for LinkedIn and Twitter/X content.

    The lifecycle is:

    1. ``start`` -- create a session, optionally load corpus & analyze style.
    2. ``generate`` -- produce content in a single LLM call, validate, retry
       on platform-limit violations.
    3. ``regenerate`` -- re-generate with optional user feedback.
    4. ``finalize`` -- mark the session complete and return final text.

    All methods return immediately so the caller retains control between
    steps (non-blocking design).
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
            session_manager: Session persistence manager.  When *None*, a
                new ``SessionManager`` is created with the active settings.
            backend: LLM backend for generation calls.  When *None*,
                ``get_backend()`` selects the default backend.
            settings: Writer settings.  When *None*, settings are loaded
                via ``load_settings()``.
        """
        self._settings: WriterSettings = settings if settings is not None else load_settings()
        self._session_manager: SessionManager = (
            session_manager
            if session_manager is not None
            else SessionManager(settings=self._settings)
        )
        self._backend: LLMBackend = backend if backend is not None else get_backend()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(
        self,
        *,
        content_type: ContentType,
        instruction: str,
        corpus_dir: Path | None = None,
        example_files: list[str] | None = None,
    ) -> SessionState:
        """Create a session and optionally run corpus-based style analysis.

        Args:
            content_type: Must be ``LINKEDIN`` or ``TWITTER``.
            instruction: The user's writing instruction or topic.
            corpus_dir: Optional directory containing reference documents
                for style analysis.
            example_files: Optional filenames within *corpus_dir* to use
                as few-shot examples.

        Returns:
            A ``SessionState`` in ``ANALYZING`` status.

        Raises:
            ValueError: If *content_type* is not a short-form type.
        """
        if content_type not in _SHORT_FORM_TYPES:
            msg = (
                f"ShortFormWorkflow only supports {[t.value for t in _SHORT_FORM_TYPES]}, "
                f"got {content_type.value!r}."
            )
            raise ValueError(msg)

        session = self._session_manager.create(
            content_type=content_type,
            instruction=instruction,
            corpus_dir=corpus_dir,
        )

        # Optionally load corpus and run style analysis.
        if corpus_dir is not None:
            style_profile = self._analyze_corpus(corpus_dir, example_files)
            if style_profile is not None:
                self._session_manager.set_style_profile(session, style_profile)

        logger.info(
            "Short-form session started: %s (%s)",
            session.session_id,
            content_type.value,
        )
        return session

    def generate(self, session: SessionState) -> GenerationResult:
        """Generate content in a single prompt with platform validation.

        If validation fails, the workflow re-prompts the LLM with specific
        constraint violations (up to 2 retries).  The result is saved to
        the session and the status moves to ``REVIEWING``.

        Args:
            session: An active session (typically in ``ANALYZING`` status).

        Returns:
            A ``GenerationResult`` containing the generated content.
        """
        prompt = self._build_prompt(session)
        raw_content = self._backend.generate(prompt.user_prompt, system=prompt.system_prompt)

        # Validate and retry on platform-limit violations.
        content = self._validate_and_retry(session, raw_content)

        result = GenerationResult(
            content=content,
            section_name=session.content_type.value,
        )

        # Persist result and advance status.
        session.sections = [result]
        session.running_context = content
        self._session_manager.set_status(session, SessionStatus.REVIEWING)
        self._session_manager.save(session)

        logger.info("Content generated for session %s.", session.session_id)
        return result

    def regenerate(
        self,
        session: SessionState,
        *,
        feedback: str = "",
    ) -> GenerationResult:
        """Regenerate content with optional user feedback.

        Clears the previous result and produces a fresh generation.  When
        *feedback* is provided it is appended to the instruction so the
        LLM can address the user's concerns.

        Args:
            session: An active session (typically in ``REVIEWING`` status).
            feedback: Optional free-text feedback explaining why the
                previous output was rejected.

        Returns:
            A new ``GenerationResult`` with the regenerated content.
        """
        # Clear previous result.
        session.sections = []
        session.running_context = ""

        # Temporarily augment instruction with feedback.
        original_instruction = session.instruction
        if feedback:
            session.instruction = (
                f"{session.instruction}\n\nUser feedback on previous draft:\n{feedback}"
            )

        try:
            result = self.generate(session)
        finally:
            # Restore original instruction so feedback does not accumulate.
            session.instruction = original_instruction
            self._session_manager.save(session)

        return result

    def finalize(self, session: SessionState) -> str:
        """Mark the session complete and return the final content.

        Args:
            session: A session in ``REVIEWING`` status with at least one
                generated result.

        Returns:
            The final content text.

        Raises:
            ValueError: If no content has been generated yet.
        """
        if not session.sections:
            msg = "Cannot finalize: no content has been generated."
            raise ValueError(msg)

        self._session_manager.set_status(session, SessionStatus.COMPLETE)
        logger.info("Session %s finalized.", session.session_id)
        return session.sections[-1].content

    def get_status(self, session: SessionState) -> dict[str, object]:
        """Return a summary of the session's current state.

        Args:
            session: The session to inspect.

        Returns:
            A dict with keys ``content_type``, ``status``, ``has_result``,
            and ``validation_errors``.
        """
        validation_errors: list[str] = []
        if session.sections:
            errors = validate_content(session.content_type, session.sections[-1].content)
            validation_errors = [e.message for e in errors if e.severity == "error"]

        return {
            "content_type": session.content_type.value,
            "status": session.status.value,
            "has_result": bool(session.sections),
            "validation_errors": validation_errors,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_and_retry(
        self,
        session: SessionState,
        content: str,
        *,
        max_retries: int = 2,
    ) -> str:
        """Validate content and re-prompt if platform rules are violated.

        Args:
            session: The active session (used for content type).
            content: The generated text to validate.
            max_retries: Maximum number of retry attempts.

        Returns:
            Valid content, or the best attempt after *max_retries*.
        """
        prompt = self._build_prompt(session)

        for attempt in range(max_retries):
            errors = validate_content(session.content_type, content)
            error_level = [e for e in errors if e.severity == "error"]
            if not error_level:
                return content

            logger.info(
                "Validation failed (attempt %d/%d) for session %s: %s",
                attempt + 1,
                max_retries,
                session.session_id,
                [e.message for e in error_level],
            )

            retry_prompt = self._build_retry_prompt(
                prompt.user_prompt,
                content,
                [e.message for e in error_level],
            )
            content = self._backend.generate(retry_prompt)

        return content

    def _build_retry_prompt(
        self,
        original_prompt: str,
        content: str,
        errors: list[str],
    ) -> str:
        """Construct a retry prompt with the original content and violations.

        Args:
            original_prompt: The prompt used for the initial generation.
            content: The content that failed validation.
            errors: Human-readable descriptions of the validation failures.

        Returns:
            A prompt instructing the LLM to fix the specific violations.
        """
        error_list = "\n".join(f"  - {e}" for e in errors)
        return (
            f"The following content was generated but violates platform constraints:\n\n"
            f"---\n{content}\n---\n\n"
            f"Validation errors:\n{error_list}\n\n"
            f"Please revise the content to fix ALL of the above violations while "
            f"preserving the original intent and style.\n\n"
            f"Original instructions:\n{original_prompt}"
        )

    def _build_prompt(self, session: SessionState) -> AssembledPrompt:
        """Assemble the generation prompt for the session.

        Args:
            session: The active session.

        Returns:
            An ``AssembledPrompt`` ready for LLM submission.
        """
        return assemble_prompt(
            content_type=session.content_type,
            instruction=session.instruction,
            style_profile=session.style_profile,
            settings=self._settings,
        )

    def _analyze_corpus(
        self,
        corpus_dir: Path,
        example_files: list[str] | None = None,
    ) -> StyleProfile | None:
        """Load a corpus and run style analysis.

        When *example_files* are provided they are logged for traceability;
        the actual few-shot selection is handled later during prompt assembly.

        Args:
            corpus_dir: Path to the directory containing reference documents.
            example_files: Optional filenames within *corpus_dir* selected by
                the user as few-shot examples.  Logged for traceability.

        Returns:
            A ``StyleProfile`` if analysis succeeds, or ``None`` on failure.
        """
        from writing.corpus import Corpus  # noqa: PLC0415
        from writing.style import analyze_style  # noqa: PLC0415

        if example_files:
            logger.debug("User-selected example files: %s", example_files)

        try:
            corpus = Corpus(corpus_dir).load()
        except FileNotFoundError:
            logger.warning("Corpus directory not found: %s", corpus_dir)
            return None

        if len(corpus) == 0:
            logger.warning("Corpus directory is empty: %s", corpus_dir)
            return None

        return analyze_style(corpus, backend=self._backend)
