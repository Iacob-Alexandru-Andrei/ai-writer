"""High-level writing pipeline that routes to long-form or short-form workflows.

Provides a unified ``Pipeline`` facade over :class:`LongFormWorkflow` and
:class:`ShortFormWorkflow`.  Content type determines which workflow handles
each operation -- papers, theses, and blogs follow the outline-then-section
path while LinkedIn and Twitter content uses single-generation with review.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from writing.backends import resolve_backend
from writing.llm_config import StageType
from writing.models import ContentType, GenerationResult, SessionState
from writing.session import SessionManager
from writing.settings import WriterSettings, load_settings
from writing.workflows.long_form import LongFormWorkflow
from writing.workflows.short_form import ShortFormWorkflow

if TYPE_CHECKING:
    from pathlib import Path

    from writing.backends import LLMBackend

logger = logging.getLogger(__name__)

_LONG_FORM_TYPES: set[ContentType] = {
    ContentType.PAPER,
    ContentType.THESIS,
    ContentType.BLOG,
}
"""Content types routed to the long-form outline-then-section workflow."""

_SHORT_FORM_TYPES: set[ContentType] = {
    ContentType.LINKEDIN,
    ContentType.TWITTER,
}
"""Content types routed to the single-generation short-form workflow."""


class Pipeline:
    """Unified writing pipeline that delegates to the appropriate workflow.

    Routes each operation to either :class:`LongFormWorkflow` or
    :class:`ShortFormWorkflow` based on the session's content type.
    All five content types (paper, thesis, blog, linkedin, twitter)
    are supported.
    """

    def __init__(
        self,
        *,
        backend: LLMBackend | None = None,
        settings: WriterSettings | None = None,
        llm_overrides: dict[str, str] | None = None,
    ) -> None:
        """Initialise the pipeline with optional dependency overrides.

        Args:
            backend: LLM backend for text generation.  When *None*,
                backends are resolved lazily per stage.
            settings: Writer settings.  When *None*, settings are loaded
                via ``load_settings()``.
            llm_overrides: Optional LLM routing overrides passed through
                to ``load_settings()`` when *backend* is *None* and
                *settings* is not provided.
        """
        if backend is not None:
            self._explicit_backend: LLMBackend | None = backend
            self._settings = settings if settings is not None else load_settings()
        else:
            self._explicit_backend = None
            self._settings = (
                settings
                if settings is not None
                else load_settings(llm_overrides=llm_overrides)
            )
        self._llm_settings = self._settings.llm
        self._session_manager = SessionManager(settings=self._settings)
        if self._explicit_backend is not None:
            self._long_form = LongFormWorkflow(
                session_manager=self._session_manager,
                backend=self._explicit_backend,
                settings=self._settings,
            )
            self._short_form = ShortFormWorkflow(
                session_manager=self._session_manager,
                backend=self._explicit_backend,
                settings=self._settings,
            )
        else:
            self._long_form = LongFormWorkflow(
                session_manager=self._session_manager,
                backend_resolver=self._resolve_backend_for_stage,
                settings=self._settings,
            )
            self._short_form = ShortFormWorkflow(
                session_manager=self._session_manager,
                backend_resolver=self._resolve_backend_for_stage,
                settings=self._settings,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_session(
        self,
        *,
        content_type: ContentType,
        instruction: str,
        corpus_dir: Path | None = None,
        bibliography_path: Path | None = None,
        example_files: list[str] | None = None,
    ) -> SessionState:
        """Create a new writing session and run initial analysis.

        Routes to the appropriate workflow's ``start`` method based on the
        content type.  Long-form types require a *corpus_dir*; short-form
        types accept it optionally for style analysis.

        Args:
            content_type: The kind of document to generate.
            instruction: User-provided writing instruction or topic.
            corpus_dir: Path to the directory containing reference documents.
            bibliography_path: Optional path to a BibTeX or Markdown
                bibliography file (long-form only).
            example_files: Optional filenames within *corpus_dir* to use
                as few-shot examples.

        Returns:
            A ``SessionState`` in ``ANALYZING`` status.
        """
        if self._is_long_form(content_type):
            if corpus_dir is None:
                msg = (
                    f"Long-form content type {content_type.value!r} requires "
                    f"a corpus_dir, but None was provided."
                )
                raise ValueError(msg)
            return self._long_form.start(
                content_type=content_type,
                instruction=instruction,
                corpus_dir=corpus_dir,
                bibliography_path=bibliography_path,
                example_files=example_files,
            )
        return self._short_form.start(
            content_type=content_type,
            instruction=instruction,
            corpus_dir=corpus_dir,
            example_files=example_files,
        )

    def generate_outline(self, session: SessionState) -> list[str]:
        """Generate a document outline for a long-form session.

        Only valid for long-form content types (paper, thesis, blog).

        Args:
            session: An active session in ``ANALYZING`` status.

        Returns:
            Ordered list of section titles comprising the outline.

        Raises:
            ValueError: If the session's content type is short-form.
        """
        if not self._is_long_form(session.content_type):
            msg = (
                f"Outline generation is only supported for long-form types "
                f"{[t.value for t in _LONG_FORM_TYPES]}, "
                f"got {session.content_type.value!r}."
            )
            raise ValueError(msg)
        return self._long_form.generate_outline(session)

    def generate_next(self, session: SessionState) -> GenerationResult:
        """Generate the next piece of content for the session.

        For long-form types, generates the next outline section.  For
        short-form types, produces the full content in a single call.

        Args:
            session: An active session with remaining content to generate.

        Returns:
            A ``GenerationResult`` for the generated content.
        """
        workflow = self._get_workflow(session.content_type)
        if isinstance(workflow, LongFormWorkflow):
            return workflow.generate_section(session)
        return workflow.generate(session)

    def regenerate(
        self,
        session: SessionState,
        *,
        feedback: str = "",
    ) -> GenerationResult:
        """Regenerate content with optional user feedback.

        For short-form types, delegates to ``ShortFormWorkflow.regenerate``.
        For long-form types, decrements the section index and re-generates
        the current section with feedback incorporated into the instruction.

        Args:
            session: An active session with at least one generated result.
            feedback: Optional free-text feedback explaining why the
                previous output was rejected.

        Returns:
            A new ``GenerationResult`` with the regenerated content.
        """
        workflow = self._get_workflow(session.content_type)
        if isinstance(workflow, ShortFormWorkflow):
            return workflow.regenerate(session, feedback=feedback)

        # Long-form: remove the last section and re-generate.
        if session.sections:
            session.sections.pop()
            session.current_section_index = max(0, session.current_section_index - 1)

        # Temporarily augment instruction with feedback.
        original_instruction = session.instruction
        if feedback:
            session.instruction = (
                f"{session.instruction}\n\nUser feedback on previous draft:\n{feedback}"
            )
        try:
            result = workflow.generate_section(session)
        finally:
            session.instruction = original_instruction
            self._session_manager.save(session)
        return result

    def finalize(self, session: SessionState) -> str:
        """Assemble and return the final document, marking the session complete.

        Routes to the appropriate workflow's ``finalize`` method.

        Args:
            session: A session with all content generated.

        Returns:
            The final document text.
        """
        workflow = self._get_workflow(session.content_type)
        return workflow.finalize(session)

    def get_status(self, session: SessionState) -> dict[str, object]:
        """Return a summary of the session's current workflow state.

        Routes to the appropriate workflow's ``get_status`` method.

        Args:
            session: The session to inspect.

        Returns:
            A dict describing the session's progress and state.
        """
        workflow = self._get_workflow(session.content_type)
        return workflow.get_status(session)

    def _resolve_backend_for_stage(self, stage: StageType) -> LLMBackend:
        """Resolve the backend for a workflow stage."""
        if self._explicit_backend is not None:
            return self._explicit_backend
        return resolve_backend(stage, self._llm_settings)

    def resume_session(self, session_id: str) -> SessionState:
        """Load and return a previously persisted session.

        Args:
            session_id: Identifier of the session to resume.

        Returns:
            The loaded ``SessionState``.

        Raises:
            FileNotFoundError: If the session does not exist on disk.
        """
        return self._session_manager.load(session_id)

    def list_sessions(self) -> list[dict[str, str]]:
        """Return summary metadata for all persisted sessions.

        Returns:
            A list of dicts with keys ``session_id``, ``content_type``,
            ``instruction``, ``status``, and ``created_at``.
        """
        return self._session_manager.list_sessions()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_workflow(self, content_type: ContentType) -> LongFormWorkflow | ShortFormWorkflow:
        """Return the workflow instance for the given content type.

        Args:
            content_type: The content type to route.

        Returns:
            The ``LongFormWorkflow`` or ``ShortFormWorkflow`` instance.
        """
        if self._is_long_form(content_type):
            return self._long_form
        return self._short_form

    @staticmethod
    def _is_long_form(content_type: ContentType) -> bool:
        """Check whether a content type uses the long-form workflow.

        Args:
            content_type: The content type to check.

        Returns:
            ``True`` if the content type is in ``_LONG_FORM_TYPES``.
        """
        return content_type in _LONG_FORM_TYPES
