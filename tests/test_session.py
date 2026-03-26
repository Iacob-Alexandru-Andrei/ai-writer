"""Unit tests for writing.session.SessionManager."""

from __future__ import annotations

import time

import pytest
from writing.models import (
    ContentType,
    GenerationResult,
    SessionStatus,
    StyleProfile,
)
from writing.session import SessionManager
from writing.settings import WriterSettings


@pytest.fixture
def manager(tmp_path) -> SessionManager:
    """Return a SessionManager backed by a temporary cache directory."""
    settings = WriterSettings(cache_dir=tmp_path / "sessions")
    return SessionManager(settings=settings)


class TestCreate:
    """Tests for SessionManager.create()."""

    def test_returns_valid_session_state(self, manager) -> None:
        session = manager.create(
            content_type=ContentType.PAPER,
            instruction="Write about transformers",
        )
        assert session.content_type == ContentType.PAPER
        assert session.instruction == "Write about transformers"

    def test_generates_unique_id(self, manager) -> None:
        s1 = manager.create(content_type=ContentType.BLOG, instruction="a")
        s2 = manager.create(content_type=ContentType.BLOG, instruction="b")
        assert s1.session_id != s2.session_id

    def test_id_is_nonempty_string(self, manager) -> None:
        session = manager.create(content_type=ContentType.PAPER, instruction="x")
        assert isinstance(session.session_id, str)
        assert len(session.session_id) > 0

    def test_persists_to_disk_on_create(self, manager) -> None:
        session = manager.create(content_type=ContentType.THESIS, instruction="y")
        path = manager.session_dir(session.session_id) / "session.json"
        assert path.exists()


class TestSaveAndLoad:
    """Tests for save/load roundtrip."""

    def test_roundtrip(self, manager) -> None:
        original = manager.create(
            content_type=ContentType.PAPER,
            instruction="Test instruction",
        )
        loaded = manager.load(original.session_id)
        assert loaded.session_id == original.session_id
        assert loaded.content_type == original.content_type
        assert loaded.instruction == original.instruction

    def test_load_nonexistent_raises(self, manager) -> None:
        with pytest.raises(FileNotFoundError):
            manager.load("nonexistent_session_id")

    def test_save_updates_timestamp(self, manager) -> None:
        session = manager.create(content_type=ContentType.BLOG, instruction="ts test")
        old_ts = session.updated_at
        time.sleep(0.01)
        manager.save(session)
        loaded = manager.load(session.session_id)
        assert loaded.updated_at > old_ts


class TestAdvance:
    """Tests for SessionManager.advance()."""

    def test_appends_result_and_increments_index(self, manager) -> None:
        session = manager.create(content_type=ContentType.PAPER, instruction="adv")
        assert session.current_section_index == 0
        assert len(session.sections) == 0

        result = GenerationResult(
            content="Introduction text here.",
            section_name="Introduction",
            token_count=10,
        )
        advanced = manager.advance(session, result)

        assert advanced.current_section_index == 1
        assert len(advanced.sections) == 1
        assert advanced.sections[0].section_name == "Introduction"
        assert advanced.running_context == "Introduction text here."

    def test_advance_persists(self, manager) -> None:
        session = manager.create(content_type=ContentType.PAPER, instruction="adv p")
        result = GenerationResult(content="Content.", section_name="Sec1")
        manager.advance(session, result)

        loaded = manager.load(session.session_id)
        assert loaded.current_section_index == 1
        assert len(loaded.sections) == 1


class TestMutationHelpers:
    """Tests for set_status, set_outline, set_style_profile."""

    def test_set_status(self, manager) -> None:
        session = manager.create(content_type=ContentType.PAPER, instruction="status")
        assert session.status == SessionStatus.ANALYZING

        updated = manager.set_status(session, SessionStatus.GENERATING)
        assert updated.status == SessionStatus.GENERATING

        loaded = manager.load(session.session_id)
        assert loaded.status == SessionStatus.GENERATING

    def test_set_outline(self, manager) -> None:
        session = manager.create(content_type=ContentType.PAPER, instruction="outline")
        outline = ["Introduction", "Methods", "Results", "Discussion"]
        updated = manager.set_outline(session, outline)
        assert updated.outline == outline

        loaded = manager.load(session.session_id)
        assert loaded.outline == outline

    def test_set_style_profile(self, manager) -> None:
        session = manager.create(content_type=ContentType.PAPER, instruction="style")
        profile = StyleProfile(
            vocabulary_level="advanced",
            tone="formal",
            paragraph_structure="topic-evidence-conclusion",
        )
        updated = manager.set_style_profile(session, profile)
        assert updated.style_profile is not None
        assert updated.style_profile.vocabulary_level == "advanced"

        loaded = manager.load(session.session_id)
        assert loaded.style_profile is not None
        assert loaded.style_profile.tone == "formal"


class TestListSessions:
    """Tests for SessionManager.list_sessions()."""

    def test_empty_cache(self, manager) -> None:
        assert manager.list_sessions() == []

    def test_returns_all_sessions(self, manager) -> None:
        manager.create(content_type=ContentType.PAPER, instruction="a")
        manager.create(content_type=ContentType.BLOG, instruction="b")
        manager.create(content_type=ContentType.THESIS, instruction="c")

        listing = manager.list_sessions()
        assert len(listing) == 3
        instructions = {item["instruction"] for item in listing}
        assert instructions == {"a", "b", "c"}

    def test_listing_contains_expected_keys(self, manager) -> None:
        manager.create(content_type=ContentType.PAPER, instruction="meta")
        listing = manager.list_sessions()
        assert len(listing) == 1
        entry = listing[0]
        assert "session_id" in entry
        assert "content_type" in entry
        assert "instruction" in entry
        assert "status" in entry
        assert "created_at" in entry


class TestGetLatest:
    """Tests for SessionManager.get_latest()."""

    def test_empty_cache_returns_none(self, manager) -> None:
        assert manager.get_latest() is None

    def test_returns_most_recently_updated(self, manager) -> None:
        s1 = manager.create(content_type=ContentType.PAPER, instruction="first")
        time.sleep(0.02)
        _s2 = manager.create(content_type=ContentType.BLOG, instruction="second")
        time.sleep(0.02)
        # Update s1 so it becomes the latest
        manager.set_status(s1, SessionStatus.COMPLETE)

        latest = manager.get_latest()
        assert latest is not None
        assert latest.session_id == s1.session_id

    def test_returns_single_session(self, manager) -> None:
        s = manager.create(content_type=ContentType.PAPER, instruction="only")
        latest = manager.get_latest()
        assert latest is not None
        assert latest.session_id == s.session_id


class TestDelete:
    """Tests for SessionManager.delete()."""

    def test_removes_session_directory(self, manager) -> None:
        session = manager.create(content_type=ContentType.PAPER, instruction="del")
        sid = session.session_id
        assert manager.session_dir(sid).exists()

        result = manager.delete(sid)
        assert result is True
        assert not manager.session_dir(sid).exists()

    def test_delete_nonexistent_returns_false(self, manager) -> None:
        result = manager.delete("no_such_session")
        assert result is False

    def test_load_after_delete_raises(self, manager) -> None:
        session = manager.create(content_type=ContentType.PAPER, instruction="del2")
        manager.delete(session.session_id)
        with pytest.raises(FileNotFoundError):
            manager.load(session.session_id)
