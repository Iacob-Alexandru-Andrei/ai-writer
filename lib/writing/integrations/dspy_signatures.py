"""DSPy Signature classes for structured LLM prompting, one per content type.

DSPy is an optional dependency (``pip install ai-writer[all]``).  This module
handles ``ImportError`` gracefully: when DSPy is **not** installed every public
function still works -- signature look-ups raise a descriptive ``ImportError``
and :func:`is_available` returns ``False``.
"""

from __future__ import annotations

import contextlib
import importlib
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import types
    from collections.abc import Callable

from writing.models import ContentType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional import
# ---------------------------------------------------------------------------

_INSTALL_HINT: str = (
    "dspy-ai is not installed. "
    "Install it with:  pip install ai-writer[all]"
)

_dspy: types.ModuleType | None = None

with contextlib.suppress(ImportError):
    _dspy = importlib.import_module("dspy")

# ---------------------------------------------------------------------------
# Descriptions (kept short to stay within line-length limits)
# ---------------------------------------------------------------------------

_DESC_INSTRUCTION = "High-level writing instruction"
_DESC_STYLE = "Serialised style-profile constraints"
_DESC_SECTION = "Section title to generate"
_DESC_OUTLINE = "Document outline for structure"
_DESC_RUNNING = "Rolling summary of prior sections"
_DESC_BIB = "Serialised bibliography entries"
_DESC_EXAMPLES = "Reference examples from user corpus"
_DESC_CHAPTER = "Current chapter context and role"
_DESC_SEO = "Comma-separated SEO keywords"
_DESC_POINTS = "Comma-separated key points"
_DESC_MAX_TWEETS = "Max tweets in the thread"
_DESC_CONTENT = "Generated section body text"
_DESC_CITATIONS = "Comma-separated citation keys used"
_DESC_BLOG_CONTENT = "Generated section body text"
_DESC_POST = "Generated LinkedIn post text"
_DESC_THREAD = "Generated thread with tweet boundaries"

# ---------------------------------------------------------------------------
# Signature classes (defined only when DSPy is importable)
# ---------------------------------------------------------------------------

if _dspy is not None:
    _inp = _dspy.InputField
    _out = _dspy.OutputField

    class PaperSectionSignature(
        _dspy.Signature,
    ):
        """Generate a section of an academic paper.

        Attributes:
            instruction: High-level writing instruction or topic.
            style_profile: Serialised style-profile constraints.
            section_name: Title of the section to generate.
            outline_context: Document outline for structural awareness.
            running_context: Rolling summary of prior sections.
            bibliography_hints: Serialised bibliography entries.
            few_shot_examples: Reference examples from user corpus.
            section_content: Generated section body text.
            citations_used: Comma-separated citation keys used.
        """

        instruction: str = _inp(desc=_DESC_INSTRUCTION)
        style_profile: str = _inp(desc=_DESC_STYLE)
        section_name: str = _inp(desc=_DESC_SECTION)
        outline_context: str = _inp(desc=_DESC_OUTLINE)
        running_context: str = _inp(desc=_DESC_RUNNING)
        bibliography_hints: str = _inp(desc=_DESC_BIB)
        few_shot_examples: str = _inp(desc=_DESC_EXAMPLES)
        section_content: str = _out(desc=_DESC_CONTENT)
        citations_used: str = _out(desc=_DESC_CITATIONS)

    class ThesisSectionSignature(
        _dspy.Signature,
    ):
        """Generate a section of a thesis chapter.

        Attributes:
            instruction: High-level writing instruction or topic.
            style_profile: Serialised style-profile constraints.
            section_name: Title of the section to generate.
            outline_context: Document outline for structural awareness.
            running_context: Rolling summary of prior sections.
            bibliography_hints: Serialised bibliography entries.
            chapter_context: Current chapter context and role.
            few_shot_examples: Reference examples from user corpus.
            section_content: Generated section body text.
            citations_used: Comma-separated citation keys used.
        """

        instruction: str = _inp(desc=_DESC_INSTRUCTION)
        style_profile: str = _inp(desc=_DESC_STYLE)
        section_name: str = _inp(desc=_DESC_SECTION)
        outline_context: str = _inp(desc=_DESC_OUTLINE)
        running_context: str = _inp(desc=_DESC_RUNNING)
        bibliography_hints: str = _inp(desc=_DESC_BIB)
        chapter_context: str = _inp(desc=_DESC_CHAPTER)
        few_shot_examples: str = _inp(desc=_DESC_EXAMPLES)
        section_content: str = _out(desc=_DESC_CONTENT)
        citations_used: str = _out(desc=_DESC_CITATIONS)

    class BlogSectionSignature(
        _dspy.Signature,
    ):
        """Generate a section of a blog post.

        Attributes:
            instruction: High-level writing instruction or topic.
            style_profile: Serialised style-profile constraints.
            section_name: Title of the section to generate.
            seo_keywords: Comma-separated SEO keywords to incorporate.
            section_content: Generated section body text.
        """

        instruction: str = _inp(desc=_DESC_INSTRUCTION)
        style_profile: str = _inp(desc=_DESC_STYLE)
        section_name: str = _inp(desc=_DESC_SECTION)
        seo_keywords: str = _inp(desc=_DESC_SEO)
        section_content: str = _out(desc=_DESC_BLOG_CONTENT)

    class LinkedInPostSignature(
        _dspy.Signature,
    ):
        """Generate a LinkedIn post.

        Attributes:
            instruction: High-level writing instruction or topic.
            style_profile: Serialised style-profile constraints.
            key_points: Comma-separated key points to cover.
            post_content: Generated LinkedIn post text.
        """

        instruction: str = _inp(desc=_DESC_INSTRUCTION)
        style_profile: str = _inp(desc=_DESC_STYLE)
        key_points: str = _inp(desc=_DESC_POINTS)
        post_content: str = _out(desc=_DESC_POST)

    class TwitterThreadSignature(
        _dspy.Signature,
    ):
        """Generate a Twitter/X thread.

        Attributes:
            instruction: High-level writing instruction or topic.
            style_profile: Serialised style-profile constraints.
            key_points: Comma-separated key points to cover.
            max_tweets: Maximum number of tweets in the thread.
            thread_content: Generated thread content with tweet boundaries.
        """

        instruction: str = _inp(desc=_DESC_INSTRUCTION)
        style_profile: str = _inp(desc=_DESC_STYLE)
        key_points: str = _inp(desc=_DESC_POINTS)
        max_tweets: str = _inp(desc=_DESC_MAX_TWEETS)
        thread_content: str = _out(desc=_DESC_THREAD)

else:
    # ----- Stub classes when DSPy is NOT installed -----

    class PaperSectionSignature:  # type: ignore[no-redef]
        """Stub for :class:`PaperSectionSignature` when DSPy is absent."""

        def __init_subclass__(cls, **kwargs: object) -> None:
            """Raise on subclassing -- DSPy is required."""
            raise ImportError(_INSTALL_HINT)

        def __init__(self) -> None:
            """Raise on instantiation -- DSPy is required."""
            raise ImportError(_INSTALL_HINT)

    class ThesisSectionSignature:  # type: ignore[no-redef]
        """Stub for :class:`ThesisSectionSignature` when DSPy is absent."""

        def __init_subclass__(cls, **kwargs: object) -> None:
            """Raise on subclassing -- DSPy is required."""
            raise ImportError(_INSTALL_HINT)

        def __init__(self) -> None:
            """Raise on instantiation -- DSPy is required."""
            raise ImportError(_INSTALL_HINT)

    class BlogSectionSignature:  # type: ignore[no-redef]
        """Stub for :class:`BlogSectionSignature` when DSPy is absent."""

        def __init_subclass__(cls, **kwargs: object) -> None:
            """Raise on subclassing -- DSPy is required."""
            raise ImportError(_INSTALL_HINT)

        def __init__(self) -> None:
            """Raise on instantiation -- DSPy is required."""
            raise ImportError(_INSTALL_HINT)

    class LinkedInPostSignature:  # type: ignore[no-redef]
        """Stub for :class:`LinkedInPostSignature` when DSPy is absent."""

        def __init_subclass__(cls, **kwargs: object) -> None:
            """Raise on subclassing -- DSPy is required."""
            raise ImportError(_INSTALL_HINT)

        def __init__(self) -> None:
            """Raise on instantiation -- DSPy is required."""
            raise ImportError(_INSTALL_HINT)

    class TwitterThreadSignature:  # type: ignore[no-redef]
        """Stub for :class:`TwitterThreadSignature` when DSPy is absent."""

        def __init_subclass__(cls, **kwargs: object) -> None:
            """Raise on subclassing -- DSPy is required."""
            raise ImportError(_INSTALL_HINT)

        def __init__(self) -> None:
            """Raise on instantiation -- DSPy is required."""
            raise ImportError(_INSTALL_HINT)


# ---------------------------------------------------------------------------
# Signature registry
# ---------------------------------------------------------------------------

_SIGNATURE_MAP: dict[ContentType, type] = {
    ContentType.PAPER: PaperSectionSignature,
    ContentType.THESIS: ThesisSectionSignature,
    ContentType.BLOG: BlogSectionSignature,
    ContentType.LINKEDIN: LinkedInPostSignature,
    ContentType.TWITTER: TwitterThreadSignature,
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def is_available() -> bool:
    """Check whether DSPy can be imported.

    Returns:
        ``True`` when the ``dspy`` package is importable,
        ``False`` otherwise.
    """
    return _dspy is not None


def get_signature_for_type(content_type: ContentType) -> type:
    """Return the DSPy Signature class for *content_type*.

    When DSPy is not installed the returned stub class will raise
    ``ImportError`` on instantiation.

    Args:
        content_type: The content type to look up.

    Returns:
        The corresponding Signature (or stub) class.

    Raises:
        KeyError: If no signature is registered for the given type.
    """
    try:
        return _SIGNATURE_MAP[content_type]
    except KeyError:
        msg = (
            "No DSPy signature registered for content type: "
            f"{content_type!r}"
        )
        raise KeyError(msg) from None


def create_optimizer(
    metric_fn: Callable[..., float] | None = None,
) -> object:
    """Create a DSPy optimiser for prompt tuning.

    Returns a ``dspy.BootstrapFewShot`` instance.  When no *metric_fn*
    is provided a placeholder metric that always returns ``1.0`` is used.

    Args:
        metric_fn: Optional callable
            ``(example, prediction, trace=None) -> float`` used by the
            optimiser to score candidate prompts.

    Returns:
        A ``dspy.BootstrapFewShot`` instance (or similar optimiser).

    Raises:
        ImportError: If DSPy is not installed.
    """
    if _dspy is None:
        raise ImportError(_INSTALL_HINT)

    def _default_metric(
        _example: object,
        _prediction: object,
        _trace: object = None,
    ) -> float:
        """Placeholder metric that always returns a perfect score."""
        return 1.0

    chosen_metric = metric_fn if metric_fn is not None else _default_metric
    return _dspy.BootstrapFewShot(metric=chosen_metric)
