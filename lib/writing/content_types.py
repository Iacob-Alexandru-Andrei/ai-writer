"""Content-type registry for the ai-writer system.

Provides ``ContentTypeRegistry``, a lazy-loading cache of
``ContentConfig`` objects and their associated prompt templates.  A
module-level ``registry`` singleton is exposed for convenient access.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from writing.models import ContentConfig, ContentType
from writing.settings import (
    _DEFAULT_CONFIG_DIR,
    _DEFAULT_TEMPLATE_DIR,
    load_content_config,
)

if TYPE_CHECKING:
    from pathlib import Path


class ContentTypeRegistry:
    """Lazy-loading registry that maps content types to their configs and templates.

    Configs are read from YAML files via ``settings.load_content_config``
    on first access and cached for subsequent calls.  Templates are read
    from Markdown files in the templates directory.

    Args:
        config_dir: Directory containing ``{type}.yaml`` config files.
        template_dir: Directory containing ``{type}.md`` prompt templates.
    """

    def __init__(
        self,
        config_dir: Path | None = None,
        template_dir: Path | None = None,
    ) -> None:
        """Initialise the registry with optional directory overrides.

        Args:
            config_dir: Directory containing ``{type}.yaml`` config files.
            template_dir: Directory containing ``{type}.md`` prompt templates.
        """
        self._config_dir = config_dir or _DEFAULT_CONFIG_DIR
        self._template_dir = template_dir or _DEFAULT_TEMPLATE_DIR
        self._config_cache: dict[ContentType, ContentConfig] = {}
        self._template_cache: dict[ContentType, str] = {}

    def get_config(self, content_type: ContentType) -> ContentConfig:
        """Return the configuration for *content_type*, loading on first call.

        Args:
            content_type: The content type whose config is requested.

        Returns:
            A validated ``ContentConfig`` instance.
        """
        if content_type not in self._config_cache:
            self._config_cache[content_type] = load_content_config(
                content_type,
                config_dir=self._config_dir,
            )
        return self._config_cache[content_type]

    def get_template(self, content_type: ContentType) -> str:
        """Return the prompt template for *content_type*, loading on first call.

        Args:
            content_type: The content type whose template is requested.

        Returns:
            The raw template string read from ``templates/{type}.md``.

        Raises:
            FileNotFoundError: If no template file exists for *content_type*.
        """
        if content_type not in self._template_cache:
            template_path = self._template_dir / f"{content_type.value}.md"
            self._template_cache[content_type] = template_path.read_text()
        return self._template_cache[content_type]

    def list_types(self) -> list[ContentType]:
        """Return all available content types.

        Returns:
            A list of every ``ContentType`` enum member.
        """
        return list(ContentType)

    def validate_for_type(self, content_type: ContentType, text: str) -> list[str]:
        """Validate *text* against the rules defined for *content_type*.

        Currently checks:

        * ``min_sections`` -- the text must contain at least *N* Markdown
          headings (lines starting with ``#``).
        * ``max_chars`` -- total character count must not exceed the limit.
        * ``max_chars_per_tweet`` -- when the text is split on blank lines,
          each segment must stay within the per-tweet character limit.

        Args:
            content_type: The content type whose rules apply.
            text: The document text to validate.

        Returns:
            A list of human-readable failure messages.  An empty list
            means the text passes all validation rules.
        """
        config = self.get_config(content_type)
        rules = config.validation_rules
        failures: list[str] = []

        # --- min_sections ------------------------------------------------
        min_sections = rules.get("min_sections")
        if min_sections is not None:
            heading_count = sum(1 for line in text.splitlines() if line.startswith("#"))
            if heading_count < int(min_sections):
                failures.append(
                    f"Expected at least {min_sections} section headings, "
                    f"found {heading_count}."
                )

        # --- max_chars ---------------------------------------------------
        max_chars = rules.get("max_chars")
        if max_chars is not None and len(text) > int(max_chars):
            failures.append(
                f"Text length ({len(text)} chars) exceeds maximum of {max_chars}."
            )

        # --- max_chars_per_tweet -----------------------------------------
        max_per_tweet = rules.get("max_chars_per_tweet")
        if max_per_tweet is not None:
            limit = int(max_per_tweet)
            segments = [s.strip() for s in text.split("\n\n") if s.strip()]
            for idx, segment in enumerate(segments, start=1):
                if len(segment) > limit:
                    failures.append(
                        f"Tweet {idx} is {len(segment)} chars, "
                        f"exceeding the {limit}-char limit."
                    )

        return failures


registry: ContentTypeRegistry = ContentTypeRegistry()
"""Module-level singleton registry instance."""
