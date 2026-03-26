"""Pydantic models for structured LLM output, one per content type.

These models define the expected shape of generated content.  They are plain
Pydantic ``BaseModel`` subclasses and do **not** depend on the ``instructor``
library at import time -- ``instructor`` is an optional integration that can
use these models for constrained decoding when available.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from writing.models import ContentType

# ---------------------------------------------------------------------------
# Academic
# ---------------------------------------------------------------------------


class AcademicSection(BaseModel):
    """A single section within an academic document.

    Attributes:
        title: Section heading (e.g. "Introduction").
        content: Body text of the section.
        citations: Citation keys referenced in this section.
    """

    title: str
    content: str
    citations: list[str] = Field(default_factory=list)


class AcademicPaper(BaseModel):
    """Structured representation of a complete academic paper.

    Attributes:
        abstract: Paper abstract.
        sections: Ordered list of paper sections.
        bibliography_keys: All citation keys used across the paper.
    """

    abstract: str
    sections: list[AcademicSection] = Field(default_factory=list)
    bibliography_keys: list[str] = Field(default_factory=list)


class ThesisChapter(BaseModel):
    """A single chapter of a thesis document.

    Attributes:
        chapter_title: Title of the chapter.
        sections: Sections within the chapter.
        chapter_number: Ordinal position of the chapter.
    """

    chapter_title: str
    sections: list[AcademicSection] = Field(default_factory=list)
    chapter_number: int


# ---------------------------------------------------------------------------
# Social / Blog
# ---------------------------------------------------------------------------


class BlogPost(BaseModel):
    """Structured representation of a blog post.

    Attributes:
        title: Blog post title.
        meta_description: SEO meta description.
        sections: Ordered list of sections (hook, body, conclusion).
        word_count: Total word count of the post.
    """

    title: str
    meta_description: str
    sections: list[AcademicSection] = Field(default_factory=list)
    word_count: int


class LinkedInPost(BaseModel):
    """Structured representation of a LinkedIn post.

    Attributes:
        hook: Opening line designed to capture attention.
        body: Main content of the post.
        cta: Optional call-to-action closing line.
        total_chars: Total character count of the post.
    """

    hook: str
    body: str
    cta: str = ""
    total_chars: int


class TwitterThread(BaseModel):
    """Structured representation of a Twitter/X thread.

    Attributes:
        tweets: Ordered list of individual tweet texts.
        thread_topic: Brief label describing the thread topic.
    """

    tweets: list[str] = Field(default_factory=list)
    thread_topic: str


# ---------------------------------------------------------------------------
# Registry helper
# ---------------------------------------------------------------------------

_MODEL_MAP: dict[ContentType, type[BaseModel]] = {
    ContentType.PAPER: AcademicPaper,
    ContentType.THESIS: ThesisChapter,
    ContentType.BLOG: BlogPost,
    ContentType.LINKEDIN: LinkedInPost,
    ContentType.TWITTER: TwitterThread,
}


def get_model_for_type(content_type: ContentType) -> type[BaseModel]:
    """Return the Pydantic model class appropriate for *content_type*.

    Args:
        content_type: The content type to look up.

    Returns:
        The corresponding ``BaseModel`` subclass.

    Raises:
        KeyError: If no model is registered for the given content type.
    """
    try:
        return _MODEL_MAP[content_type]
    except KeyError:
        msg = f"No instructor model registered for content type: {content_type!r}"
        raise KeyError(msg) from None
