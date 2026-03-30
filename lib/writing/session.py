"""Writing session lifecycle management with disk persistence.

Provides ``SessionManager`` for creating, loading, saving, and advancing
writing sessions.  Session state is serialised as JSON (via Pydantic v2)
under ``{cache_dir}/{session_id}/session.json``.
"""

from __future__ import annotations

import logging
import shutil
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from writing.llm_config import LLMSettings
from writing.models import ContentType, SessionState, SessionStatus
from writing.settings import WriterSettings, load_settings

if TYPE_CHECKING:
    from pathlib import Path

    from writing.models import GenerationResult, StyleProfile

logger = logging.getLogger(__name__)

_SESSION_FILENAME = "session.json"


class SessionManager:
    """Create, persist, and mutate writing sessions on disk.

    Sessions are stored as ``{cache_dir}/{session_id}/session.json``.  The
    session directory is created lazily on the first call to :meth:`save`.

    Attributes:
        settings: Active writer settings instance.
    """

    def __init__(self, settings: WriterSettings | None = None) -> None:
        """Initialise the manager, creating the cache directory if needed.

        Args:
            settings: Writer settings to use.  When *None*, settings are
                loaded via :func:`~writing.settings.load_settings`.
        """
        self.settings: WriterSettings = settings if settings is not None else load_settings()
        self.settings.cache_dir.mkdir(parents=True, exist_ok=True)

    # -- core CRUD ---------------------------------------------------------

    def create(
        self,
        *,
        content_type: ContentType,
        instruction: str,
        corpus_dir: Path | None = None,
        bibliography_path: Path | None = None,
        llm_settings: LLMSettings | None = None,
    ) -> SessionState:
        """Create a new session, persist it, and return the state.

        Args:
            content_type: Document type to generate.
            instruction: User-provided writing instruction or topic.
            corpus_dir: Optional path to the reference-document directory.
            bibliography_path: Optional path to a BibTeX file.
            llm_settings: Optional snapshot of the resolved LLM settings.

        Returns:
            A freshly initialised ``SessionState``.
        """
        session = SessionState(
            content_type=content_type,
            instruction=instruction,
            corpus_dir=corpus_dir,
            bibliography_path=bibliography_path,
            llm_settings=llm_settings,
        )
        self.save(session)
        return session

    def load(self, session_id: str) -> SessionState:
        """Load a session from disk.

        Args:
            session_id: Identifier of the session to load.

        Returns:
            The deserialised ``SessionState``.

        Raises:
            FileNotFoundError: If the session file does not exist.
        """
        path = self.session_dir(session_id) / _SESSION_FILENAME
        if not path.exists():
            msg = f"Session not found: {path}"
            raise FileNotFoundError(msg)
        return SessionState.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, session: SessionState) -> Path:
        """Persist a session to disk, updating its ``updated_at`` timestamp.

        The session directory is created if it does not yet exist.

        Args:
            session: The session state to save.

        Returns:
            Path to the written ``session.json`` file.
        """
        session.updated_at = datetime.now(tz=UTC)
        directory = self.session_dir(session.session_id)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / _SESSION_FILENAME
        path.write_text(session.model_dump_json(indent=2), encoding="utf-8")
        return path

    def delete(self, session_id: str) -> bool:
        """Remove a session directory from disk.

        Args:
            session_id: Identifier of the session to delete.

        Returns:
            ``True`` if the directory existed and was removed, ``False``
            otherwise.
        """
        directory = self.session_dir(session_id)
        if directory.exists():
            shutil.rmtree(directory)
            return True
        return False

    # -- mutation helpers --------------------------------------------------

    def advance(self, session: SessionState, result: GenerationResult) -> SessionState:
        """Append a generation result and advance the section index.

        The result is added to ``sections``, ``current_section_index`` is
        incremented, the ``running_context`` is updated with the new
        section content, and the state is saved.

        Args:
            session: The session to advance.
            result: The generation result for the current section.

        Returns:
            The mutated (and saved) session.
        """
        session.sections.append(result)
        session.current_section_index += 1
        session.running_context = result.content
        self.save(session)
        return session

    def set_status(self, session: SessionState, status: SessionStatus) -> SessionState:
        """Update the session status and save.

        Args:
            session: The session to modify.
            status: New lifecycle status.

        Returns:
            The mutated (and saved) session.
        """
        session.status = status
        self.save(session)
        return session

    def set_outline(self, session: SessionState, outline: list[str]) -> SessionState:
        """Set the session outline and save.

        Args:
            session: The session to modify.
            outline: Ordered list of section titles.

        Returns:
            The mutated (and saved) session.
        """
        session.outline = outline
        self.save(session)
        return session

    def set_style_profile(
        self, session: SessionState, profile: StyleProfile
    ) -> SessionState:
        """Set the session's style profile and save.

        Args:
            session: The session to modify.
            profile: Extracted style profile.

        Returns:
            The mutated (and saved) session.
        """
        session.style_profile = profile
        self.save(session)
        return session

    # -- query helpers -----------------------------------------------------

    def list_sessions(self) -> list[dict[str, str]]:
        """Return summary metadata for every persisted session.

        Corrupted session files are logged and skipped.

        Returns:
            A list of dicts with keys ``session_id``, ``content_type``,
            ``instruction``, ``status``, and ``created_at``.
        """
        results: list[dict[str, str]] = []
        cache_dir = self.settings.cache_dir
        if not cache_dir.exists():
            return results

        for child in sorted(cache_dir.iterdir()):
            if not child.is_dir():
                continue
            session_file = child / _SESSION_FILENAME
            if not session_file.exists():
                continue
            try:
                state = SessionState.model_validate_json(
                    session_file.read_text(encoding="utf-8"),
                )
            except Exception:
                logger.warning("Skipping corrupted session file: %s", session_file)
                continue
            results.append(
                {
                    "session_id": state.session_id,
                    "content_type": state.content_type.value,
                    "instruction": state.instruction,
                    "status": state.status.value,
                    "created_at": state.created_at.isoformat(),
                }
            )
        return results

    def get_latest(self) -> SessionState | None:
        """Return the most recently updated session, or ``None``.

        Corrupted session files are logged and skipped.

        Returns:
            The ``SessionState`` with the newest ``updated_at``, or ``None``
            if no valid sessions exist.
        """
        latest: SessionState | None = None
        cache_dir = self.settings.cache_dir
        if not cache_dir.exists():
            return None

        for child in sorted(cache_dir.iterdir()):
            if not child.is_dir():
                continue
            session_file = child / _SESSION_FILENAME
            if not session_file.exists():
                continue
            try:
                state = SessionState.model_validate_json(
                    session_file.read_text(encoding="utf-8"),
                )
            except Exception:
                logger.warning("Skipping corrupted session file: %s", session_file)
                continue
            if latest is None or state.updated_at > latest.updated_at:
                latest = state
        return latest

    # -- path helpers ------------------------------------------------------

    def session_dir(self, session_id: str) -> Path:
        """Return the directory path for a given session.

        Args:
            session_id: Identifier of the session.

        Returns:
            ``{cache_dir}/{session_id}/``
        """
        return self.settings.cache_dir / session_id
