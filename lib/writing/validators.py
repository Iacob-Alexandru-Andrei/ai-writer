"""Platform-specific content validators for the ai-writer system.

Each content type has tailored validation rules (character limits, structural
requirements, etc.).  The public entry-points are :func:`validate_content` and
the convenience wrapper :func:`passes_validation`.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel

from writing.models import ContentType

# ---------------------------------------------------------------------------
# Validation result model
# ---------------------------------------------------------------------------


class ContentValidationError(BaseModel):
    """A single validation finding for generated content.

    Attributes:
        field: Logical area of the content the finding relates to.
        message: Human-readable description of the issue.
        severity: ``"error"`` for hard failures, ``"warning"`` for advisory notes.
    """

    field: str
    message: str
    severity: Literal["error", "warning"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_content(
    content_type: ContentType,
    text: str,
) -> list[ContentValidationError]:
    """Validate *text* against the rules for *content_type*.

    Args:
        content_type: The type of content being validated.
        text: The generated text to check.

    Returns:
        A list of :class:`ContentValidationError` instances.  An empty list
        means the content passes all checks.
    """
    validators = {
        ContentType.LINKEDIN: _validate_linkedin,
        ContentType.TWITTER: _validate_twitter,
        ContentType.BLOG: _validate_blog,
        ContentType.PAPER: _validate_paper,
        ContentType.THESIS: _validate_thesis,
    }
    validator = validators.get(content_type)
    if validator is None:
        return []
    return validator(text)


def passes_validation(content_type: ContentType, text: str) -> bool:
    """Return ``True`` if *text* has no errors for *content_type*.

    Warnings are tolerated -- only findings with ``severity="error"`` cause
    this function to return ``False``.

    Args:
        content_type: The type of content being validated.
        text: The generated text to check.

    Returns:
        ``True`` when no error-level findings exist.
    """
    errors = validate_content(content_type, text)
    return all(e.severity != "error" for e in errors)


# ---------------------------------------------------------------------------
# Per-type validators
# ---------------------------------------------------------------------------

_LINKEDIN_MAX_CHARS = 3000
_LINKEDIN_HOOK_LIMIT = 210

_TWITTER_CHAR_LIMIT = 280
_TWITTER_MAX_TWEETS = 15

_BLOG_MIN_WORDS = 1500
_BLOG_MAX_WORDS = 2500

_PAPER_REQUIRED_SECTIONS = {"abstract", "introduction", "conclusion"}
_THESIS_REQUIRED_SECTIONS = {"introduction", "conclusion"}


def _validate_linkedin(text: str) -> list[ContentValidationError]:
    """Check LinkedIn-specific constraints.

    Rules:
        * Total post must not exceed 3 000 characters.
        * The hook (first line) must fit within 210 characters.

    Args:
        text: The LinkedIn post text.

    Returns:
        Validation findings.
    """
    findings: list[ContentValidationError] = []

    if len(text) > _LINKEDIN_MAX_CHARS:
        findings.append(
            ContentValidationError(
                field="total_length",
                message=(
                    f"Post is {len(text)} characters, "
                    f"exceeding the {_LINKEDIN_MAX_CHARS}-character limit."
                ),
                severity="error",
            ),
        )

    first_line = text.split("\n", maxsplit=1)[0]
    if len(first_line) > _LINKEDIN_HOOK_LIMIT:
        findings.append(
            ContentValidationError(
                field="hook",
                message=(
                    f"Hook is {len(first_line)} characters, "
                    f"exceeding the {_LINKEDIN_HOOK_LIMIT}-character limit. "
                    "It should fit within the 'see more' fold."
                ),
                severity="warning",
            ),
        )

    return findings


def _validate_twitter(text: str) -> list[ContentValidationError]:
    """Check Twitter/X thread constraints.

    Rules:
        * Each tweet (delimited by ``---`` or newlines) must be at most 280 characters.
        * A thread may contain at most 15 tweets.

    Args:
        text: The thread text, tweets separated by ``---`` or blank lines.

    Returns:
        Validation findings.
    """
    findings: list[ContentValidationError] = []

    # Split on "---" delimiter first; fall back to double-newline.
    if "---" in text:
        tweets = [t.strip() for t in text.split("---") if t.strip()]
    else:
        tweets = [t.strip() for t in re.split(r"\n\s*\n", text) if t.strip()]

    if len(tweets) > _TWITTER_MAX_TWEETS:
        findings.append(
            ContentValidationError(
                field="thread_length",
                message=(
                    f"Thread has {len(tweets)} tweets, "
                    f"exceeding the maximum of {_TWITTER_MAX_TWEETS}."
                ),
                severity="error",
            ),
        )

    for idx, tweet in enumerate(tweets, start=1):
        if len(tweet) > _TWITTER_CHAR_LIMIT:
            findings.append(
                ContentValidationError(
                    field=f"tweet_{idx}",
                    message=(
                        f"Tweet {idx} is {len(tweet)} characters, "
                        f"exceeding the {_TWITTER_CHAR_LIMIT}-character limit."
                    ),
                    severity="error",
                ),
            )

    return findings


def _validate_blog(text: str) -> list[ContentValidationError]:
    """Check blog post constraints.

    Rules:
        * Word count should be between 1 500 and 2 500.
        * The post must contain at least one H2 heading (``## ``).

    Args:
        text: The blog post text in Markdown format.

    Returns:
        Validation findings.
    """
    findings: list[ContentValidationError] = []

    word_count = len(text.split())
    if word_count < _BLOG_MIN_WORDS:
        findings.append(
            ContentValidationError(
                field="word_count",
                message=(
                    f"Blog post is {word_count} words, "
                    f"below the minimum of {_BLOG_MIN_WORDS}."
                ),
                severity="error",
            ),
        )
    elif word_count > _BLOG_MAX_WORDS:
        findings.append(
            ContentValidationError(
                field="word_count",
                message=(
                    f"Blog post is {word_count} words, "
                    f"exceeding the maximum of {_BLOG_MAX_WORDS}."
                ),
                severity="warning",
            ),
        )

    h2_pattern = re.compile(r"^##\s+", re.MULTILINE)
    if not h2_pattern.search(text):
        findings.append(
            ContentValidationError(
                field="headings",
                message="Blog post must contain at least one H2 heading (## ...).",
                severity="error",
            ),
        )

    return findings


def _validate_paper(text: str) -> list[ContentValidationError]:
    """Check academic paper constraints.

    Rules:
        * Must contain sections for: abstract, introduction, conclusion (at minimum).

    Args:
        text: The paper text in Markdown format.

    Returns:
        Validation findings.
    """
    return _check_required_sections(text, _PAPER_REQUIRED_SECTIONS, "paper")


def _validate_thesis(text: str) -> list[ContentValidationError]:
    """Check thesis constraints.

    Rules:
        * Must contain sections for: introduction, conclusion (at minimum).

    Args:
        text: The thesis text in Markdown format.

    Returns:
        Validation findings.
    """
    return _check_required_sections(text, _THESIS_REQUIRED_SECTIONS, "thesis")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _check_required_sections(
    text: str,
    required: set[str],
    doc_type: str,
) -> list[ContentValidationError]:
    """Verify that *text* contains Markdown headings for all *required* sections.

    Section matching is case-insensitive.  A heading is any line that starts
    with one or more ``#`` characters followed by a space.

    Args:
        text: Document text in Markdown format.
        required: Set of required section names (lower-case).
        doc_type: Label used in error messages (e.g. ``"paper"``).

    Returns:
        Validation findings for any missing sections.
    """
    heading_re = re.compile(r"^#{1,6}\s+(.+)", re.MULTILINE)
    found = {m.group(1).strip().lower() for m in heading_re.finditer(text)}

    return [
        ContentValidationError(
            field="structure",
            message=f"Required {doc_type} section missing: '{section}'.",
            severity="error",
        )
        for section in sorted(required)
        if section not in found
    ]
