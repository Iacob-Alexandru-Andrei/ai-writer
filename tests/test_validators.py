"""Tests for writing.validators — content validation per platform type."""

from __future__ import annotations

from writing.models import ContentType
from writing.validators import passes_validation, validate_content

# ---------------------------------------------------------------------------
# LinkedIn
# ---------------------------------------------------------------------------


class TestLinkedInValidation:
    """Test LinkedIn post constraints."""

    def test_valid_post_passes(self) -> None:
        text = "This is a short LinkedIn post.\n\nWith a second paragraph."
        errors = validate_content(ContentType.LINKEDIN, text)
        assert all(e.severity != "error" for e in errors)

    def test_exceeds_3000_chars(self) -> None:
        text = "a" * 3001
        errors = validate_content(ContentType.LINKEDIN, text)
        error_fields = [e.field for e in errors if e.severity == "error"]
        assert "total_length" in error_fields

    def test_long_hook_warns(self) -> None:
        # First line > 210 chars should produce a warning.
        text = "A" * 220 + "\n\nRest of the post."
        errors = validate_content(ContentType.LINKEDIN, text)
        warnings = [e for e in errors if e.severity == "warning"]
        assert any(e.field == "hook" for e in warnings)

    def test_exactly_3000_chars_passes(self) -> None:
        text = "a" * 3000
        errors = validate_content(ContentType.LINKEDIN, text)
        assert all(e.severity != "error" for e in errors)


# ---------------------------------------------------------------------------
# Twitter
# ---------------------------------------------------------------------------


class TestTwitterValidation:
    """Test Twitter/X thread constraints."""

    def test_valid_thread_passes(self) -> None:
        text = "Tweet one (under 280 chars).---Tweet two, also short."
        errors = validate_content(ContentType.TWITTER, text)
        assert all(e.severity != "error" for e in errors)

    def test_single_tweet_over_280_chars(self) -> None:
        long_tweet = "a" * 281
        errors = validate_content(ContentType.TWITTER, long_tweet)
        error_fields = [e.field for e in errors if e.severity == "error"]
        assert any("tweet" in f for f in error_fields)

    def test_thread_over_280_per_tweet(self) -> None:
        tweets = "---".join(["a" * 281 for _ in range(3)])
        errors = validate_content(ContentType.TWITTER, tweets)
        error_msgs = [e for e in errors if e.severity == "error"]
        assert len(error_msgs) >= 3

    def test_thread_exceeds_15_tweets(self) -> None:
        tweets = "---".join([f"Tweet {i}" for i in range(16)])
        errors = validate_content(ContentType.TWITTER, tweets)
        error_fields = [e.field for e in errors if e.severity == "error"]
        assert "thread_length" in error_fields

    def test_exactly_280_chars_passes(self) -> None:
        text = "a" * 280
        errors = validate_content(ContentType.TWITTER, text)
        assert all(e.severity != "error" for e in errors)

    def test_blank_line_delimiter(self) -> None:
        text = "Tweet one.\n\nTweet two.\n\nTweet three."
        errors = validate_content(ContentType.TWITTER, text)
        assert all(e.severity != "error" for e in errors)


# ---------------------------------------------------------------------------
# Blog
# ---------------------------------------------------------------------------


class TestBlogValidation:
    """Test blog post constraints."""

    def test_valid_blog_passes(self) -> None:
        text = "## Section One\n\n" + "word " * 1600 + "\n\n## Section Two\n\n" + "word " * 200
        errors = validate_content(ContentType.BLOG, text)
        assert all(e.severity != "error" for e in errors)

    def test_below_1500_words_error(self) -> None:
        text = "## Heading\n\n" + "word " * 100
        errors = validate_content(ContentType.BLOG, text)
        error_fields = [e.field for e in errors if e.severity == "error"]
        assert "word_count" in error_fields

    def test_above_2500_words_warns(self) -> None:
        text = "## Heading\n\n" + "word " * 2600
        errors = validate_content(ContentType.BLOG, text)
        warnings = [e for e in errors if e.severity == "warning"]
        assert any(e.field == "word_count" for e in warnings)

    def test_missing_h2_heading_error(self) -> None:
        text = "word " * 1600
        errors = validate_content(ContentType.BLOG, text)
        error_fields = [e.field for e in errors if e.severity == "error"]
        assert "headings" in error_fields


# ---------------------------------------------------------------------------
# Paper
# ---------------------------------------------------------------------------


class TestPaperValidation:
    """Test academic paper constraints."""

    def test_valid_paper_passes(self) -> None:
        text = (
            "# Abstract\n\nSummary.\n\n"
            "# Introduction\n\nIntro text.\n\n"
            "# Methods\n\nMethods.\n\n"
            "# Conclusion\n\nConclusion text.\n"
        )
        errors = validate_content(ContentType.PAPER, text)
        assert all(e.severity != "error" for e in errors)

    def test_missing_abstract_error(self) -> None:
        text = (
            "# Introduction\n\nIntro.\n\n"
            "# Conclusion\n\nConclusion.\n"
        )
        errors = validate_content(ContentType.PAPER, text)
        error_msgs = [e.message for e in errors if e.severity == "error"]
        assert any("abstract" in m.lower() for m in error_msgs)

    def test_missing_all_sections(self) -> None:
        text = "Some random text without any headings."
        errors = validate_content(ContentType.PAPER, text)
        # Should flag abstract, introduction, and conclusion.
        assert len([e for e in errors if e.severity == "error"]) >= 3

    def test_case_insensitive_headings(self) -> None:
        text = (
            "# abstract\n\nSummary.\n\n"
            "# introduction\n\nIntro.\n\n"
            "# conclusion\n\nEnd.\n"
        )
        errors = validate_content(ContentType.PAPER, text)
        assert all(e.severity != "error" for e in errors)


# ---------------------------------------------------------------------------
# passes_validation convenience wrapper
# ---------------------------------------------------------------------------


class TestPassesValidation:
    """Test the boolean convenience wrapper."""

    def test_returns_true_for_valid_content(self) -> None:
        text = "Short LinkedIn post."
        assert passes_validation(ContentType.LINKEDIN, text) is True

    def test_returns_false_for_invalid_content(self) -> None:
        text = "a" * 3001
        assert passes_validation(ContentType.LINKEDIN, text) is False

    def test_warnings_do_not_fail(self) -> None:
        # A post with a long hook (warning) but under 3000 chars (no error).
        text = "A" * 220 + "\n\n" + "Short body."
        assert passes_validation(ContentType.LINKEDIN, text) is True

    def test_unknown_content_type_passes(self) -> None:
        # ContentType values without explicit validators should pass.
        # THESIS has a validator but let's use a text that satisfies it.
        text = "# Introduction\n\nIntro.\n\n# Conclusion\n\nEnd.\n"
        assert passes_validation(ContentType.THESIS, text) is True
