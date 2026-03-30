"""Core domain models for the ai-writer system.

Defines enums, Pydantic models, and value objects used across the writing
pipeline: content configuration, style profiles, session state, and
generation results.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from pathlib import Path  # noqa: TC003 - Pydantic needs this at runtime
from uuid import uuid4

from pydantic import BaseModel, Field
from writing.llm_config import LLMSettings


class ContentType(enum.Enum):
    """Supported content types for document generation."""

    PAPER = "paper"
    THESIS = "thesis"
    BLOG = "blog"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"


class SessionStatus(enum.Enum):
    """Lifecycle stages of a writing session."""

    ANALYZING = "analyzing"
    OUTLINING = "outlining"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    COMPLETE = "complete"


class ContentConfig(BaseModel):
    """Configuration for a specific content type.

    Loaded from ``config/{type}.yaml`` and describes the structural
    expectations, constraints, and validation rules for a document type.
    """

    sections: list[str] = Field(default_factory=list)
    constraints: dict[str, str | int | float | bool] = Field(default_factory=dict)
    output_format: str = "markdown"
    validation_rules: dict[str, str | int | float | bool] = Field(default_factory=dict)
    template_name: str = ""


class StyleProfile(BaseModel):
    """Captured writing-style fingerprint derived from user corpus analysis.

    Attributes:
        vocabulary_level: Approximate grade-level vocabulary (e.g. ``"advanced"``).
        sentence_patterns: Recurring syntactic patterns (short/long, active/passive).
        paragraph_structure: Typical paragraph layout description.
        tone: Dominant tone (formal, conversational, etc.).
        opening_patterns: Common opening strategies observed.
        closing_patterns: Common closing strategies observed.
        structural_conventions: Conventions like heading style, list usage, etc.
        raw_analysis: Full LLM analysis text preserved for debugging.
    """

    vocabulary_level: str = ""
    sentence_patterns: list[str] = Field(default_factory=list)
    paragraph_structure: str = ""
    tone: str = ""
    opening_patterns: list[str] = Field(default_factory=list)
    closing_patterns: list[str] = Field(default_factory=list)
    structural_conventions: list[str] = Field(default_factory=list)
    raw_analysis: str = ""


class FewShotExample(BaseModel):
    """A reference example extracted from the user's corpus.

    Attributes:
        source_path: Filesystem path to the source document.
        content: The extracted text content.
        section_slice: Optional section label if only a slice was taken.
        token_count: Estimated token count of ``content``.
    """

    source_path: Path
    content: str
    section_slice: str | None = None
    token_count: int = 0


class CitationEntry(BaseModel):
    """A single bibliography entry.

    Attributes:
        key: BibTeX cite key (e.g. ``"vaswani2017attention"``).
        title: Full title of the work.
        authors: Author list as a single string.
        year: Publication year.
        source_type: Source category (journal, conference, book, etc.).
    """

    key: str
    title: str
    authors: str
    year: int
    source_type: str = ""


class GenerationResult(BaseModel):
    """Output of a single section-generation step.

    Attributes:
        content: The generated text.
        section_name: Label of the section that was generated.
        token_count: Token count of the generated content.
        citations_used: Citation keys referenced in this section.
    """

    content: str
    section_name: str
    token_count: int = 0
    citations_used: list[str] = Field(default_factory=list)


def _utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(tz=UTC)


def _new_session_id() -> str:
    """Generate a fresh session identifier."""
    return uuid4().hex[:12]


class SessionState(BaseModel):
    """Persistent state for a single writing session.

    Attributes:
        session_id: Unique identifier for this session.
        content_type: The kind of document being generated.
        instruction: User-provided writing instruction or topic.
        corpus_dir: Path to the directory containing reference documents.
        bibliography_path: Optional path to a BibTeX file.
        style_profile: Extracted style profile (populated after analysis).
        outline: Generated document outline (list of section titles).
        sections: Generated section results accumulated during generation.
        running_context: Rolling summary passed between generation steps.
        llm_settings: Snapshot of the session's resolved LLM configuration.
        status: Current lifecycle stage.
        current_section_index: Index of the section being generated.
        created_at: Timestamp of session creation.
        updated_at: Timestamp of last state mutation.
    """

    session_id: str = Field(default_factory=_new_session_id)
    content_type: ContentType = ContentType.PAPER
    instruction: str = ""
    corpus_dir: Path | None = None
    bibliography_path: Path | None = None
    style_profile: StyleProfile | None = None
    outline: list[str] = Field(default_factory=list)
    sections: list[GenerationResult] = Field(default_factory=list)
    running_context: str = ""
    llm_settings: LLMSettings | None = None
    status: SessionStatus = SessionStatus.ANALYZING
    current_section_index: int = 0
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
