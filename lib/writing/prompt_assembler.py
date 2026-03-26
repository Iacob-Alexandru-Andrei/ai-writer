"""Prompt assembler for the ai-writer system.

Combines content-type template, style profile, few-shot examples, running
context, bibliography hints, and outline into a final prompt ready for LLM
submission.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from writing.content_types import registry
from writing.settings import load_settings

if TYPE_CHECKING:
    from writing.bibliography import Bibliography
    from writing.models import ContentType, FewShotExample, StyleProfile
    from writing.settings import WriterSettings


class AssembledPrompt(BaseModel):
    """A fully assembled prompt ready for LLM submission.

    Attributes:
        system_prompt: The system-level prompt text.
        user_prompt: The user-level prompt text.
        total_tokens: Estimated total token count across both prompts.
        budget_report: Tokens used per category (style_profile, few_shot, etc.).
    """

    system_prompt: str = ""
    user_prompt: str = ""
    total_tokens: int = 0
    budget_report: dict[str, int] = Field(default_factory=dict)


def _estimate_tokens(text: str) -> int:
    """Return a rough token estimate for *text*.

    Uses a simple heuristic of word count multiplied by 1.3 to approximate
    token usage for budget enforcement.

    Args:
        text: Arbitrary string to estimate.

    Returns:
        Estimated token count (always >= 0).
    """
    if not text:
        return 0
    return int(len(text.split()) * 1.3)


def _truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate *text* so its estimated token count stays within *max_tokens*.

    If truncation is necessary, the returned string ends with a
    ``[... truncated ...]`` marker so the LLM knows content was removed.

    Args:
        text: Source text.
        max_tokens: Upper token budget.

    Returns:
        The (possibly truncated) text.
    """
    if not text or _estimate_tokens(text) <= max_tokens:
        return text

    words = text.split()
    marker = "\n\n[... truncated ...]"

    # Binary search for the largest prefix that fits within budget.
    lo, hi = 0, len(words)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        candidate = " ".join(words[:mid]) + marker
        if _estimate_tokens(candidate) <= max_tokens:
            lo = mid
        else:
            hi = mid - 1

    return " ".join(words[:lo]) + marker


def _format_style_profile(profile: StyleProfile, max_tokens: int) -> str:
    """Format a style profile into a readable text block for prompt inclusion.

    Renders the profile fields into labelled sections and truncates to the
    token budget if necessary.

    Args:
        profile: The style profile to format.
        max_tokens: Maximum token budget for the formatted output.

    Returns:
        A formatted string describing the writing style.
    """
    parts: list[str] = []

    if profile.vocabulary_level:
        parts.append(f"Vocabulary Level: {profile.vocabulary_level}")
    if profile.tone:
        parts.append(f"Tone: {profile.tone}")
    if profile.paragraph_structure:
        parts.append(f"Paragraph Structure: {profile.paragraph_structure}")
    if profile.sentence_patterns:
        items = "\n".join(f"  - {p}" for p in profile.sentence_patterns)
        parts.append(f"Sentence Patterns:\n{items}")
    if profile.opening_patterns:
        items = "\n".join(f"  - {p}" for p in profile.opening_patterns)
        parts.append(f"Opening Patterns:\n{items}")
    if profile.closing_patterns:
        items = "\n".join(f"  - {p}" for p in profile.closing_patterns)
        parts.append(f"Closing Patterns:\n{items}")
    if profile.structural_conventions:
        items = "\n".join(f"  - {c}" for c in profile.structural_conventions)
        parts.append(f"Structural Conventions:\n{items}")

    text = "\n\n".join(parts)
    return _truncate_to_tokens(text, max_tokens)


def _format_few_shot_block(examples: list[FewShotExample]) -> str:
    """Format few-shot examples into a labelled block with separators.

    Each example is rendered with a header showing its source path and
    optional section slice, followed by the content.

    Args:
        examples: Pre-truncated few-shot examples to include.

    Returns:
        A formatted string containing all examples separated by dividers.
    """
    if not examples:
        return "(No examples provided.)"

    parts: list[str] = []
    for idx, ex in enumerate(examples, start=1):
        header = f"### Example {idx}: {ex.source_path.name}"
        if ex.section_slice:
            header += f" (section: {ex.section_slice})"
        parts.append(f"{header}\n\n{ex.content}")

    return "\n\n---\n\n".join(parts)


def _format_bibliography_hints(bibliography: Bibliography, max_tokens: int) -> str:
    """Format bibliography entries as concise citation hints.

    Produces a line per entry in the format:
    ``key (Authors, Year): Title``

    Args:
        bibliography: The bibliography to format.
        max_tokens: Maximum token budget for the formatted output.

    Returns:
        A formatted string listing available citations.
    """
    if not bibliography.keys:
        return "(No bibliography provided.)"

    lines: list[str] = ["Available citations:"]
    for key in bibliography.keys:
        entry = bibliography.get(key)
        if entry is None:
            continue
        lines.append(f"  - {entry.key} ({entry.authors}, {entry.year}): {entry.title}")

    text = "\n".join(lines)
    return _truncate_to_tokens(text, max_tokens)


def _format_outline_context(outline: list[str], current_section: str) -> str:
    """Format the document outline with a marker on the current section.

    Each section is listed as a numbered item.  The section matching
    *current_section* is prefixed with ``>>`` to indicate the active target.

    Args:
        outline: Full list of section titles.
        current_section: The section currently being generated.

    Returns:
        A formatted outline string with the current section highlighted.
    """
    if not outline:
        return "(No outline available.)"

    lines: list[str] = ["Document Outline:"]
    for idx, section in enumerate(outline, start=1):
        marker = ">> " if section == current_section else "   "
        lines.append(f"{marker}{idx}. {section}")

    return "\n".join(lines)


def assemble_prompt(
    *,
    content_type: ContentType,
    instruction: str,
    section_name: str = "",
    style_profile: StyleProfile | None = None,
    few_shot_examples: list[FewShotExample] | None = None,
    running_context: str = "",
    bibliography: Bibliography | None = None,
    outline: list[str] | None = None,
    settings: WriterSettings | None = None,
) -> AssembledPrompt:
    """Assemble a complete prompt from components and a content-type template.

    Loads the template for *content_type*, formats each component section
    (style profile, few-shot examples, running context, bibliography hints,
    outline), fills template placeholders via ``str.replace``, and returns
    the assembled prompt with a token budget report.

    Args:
        content_type: The type of content being generated.
        instruction: The user's writing instruction or topic.
        section_name: Name of the section to generate (empty for full docs).
        style_profile: Optional style profile to include.
        few_shot_examples: Optional pre-truncated few-shot examples.
        running_context: Rolling context from previously generated sections.
        bibliography: Optional bibliography for citation hints.
        outline: Optional document outline (list of section titles).
        settings: Optional settings override; defaults loaded when ``None``.

    Returns:
        An ``AssembledPrompt`` containing the filled template and budget report.
    """
    cfg = settings or load_settings()
    budgets = cfg.token_budgets
    budget_report: dict[str, int] = {}

    # 1. Load template.
    template = registry.get_template(content_type)

    # 2. Format style profile.
    if style_profile is not None:
        style_text = _format_style_profile(style_profile, budgets.style_profile)
    else:
        style_text = "(No style profile provided.)"
    budget_report["style_profile"] = _estimate_tokens(style_text)

    # 3. Format few-shot examples (already pre-truncated by fewshot module).
    examples = few_shot_examples or []
    fewshot_text = _format_few_shot_block(examples)
    budget_report["few_shot_examples"] = _estimate_tokens(fewshot_text)

    # 4. Format running context.
    if running_context:
        context_text = _truncate_to_tokens(running_context, budgets.running_context)
    else:
        context_text = "(No prior context.)"
    budget_report["running_context"] = _estimate_tokens(context_text)

    # 5. Format bibliography hints.
    if bibliography is not None:
        bib_text = _format_bibliography_hints(bibliography, budgets.style_profile)
    else:
        bib_text = "(No bibliography provided.)"
    budget_report["bibliography_hints"] = _estimate_tokens(bib_text)

    # 6. Format outline context.
    if outline:
        outline_text = _format_outline_context(outline, section_name)
    else:
        outline_text = "(No outline available.)"
    budget_report["outline"] = _estimate_tokens(outline_text)

    # 7. Fill template placeholders.
    filled = template
    filled = filled.replace("{{ style_profile }}", style_text)
    filled = filled.replace("{{ instruction }}", instruction)
    filled = filled.replace("{{ section_name }}", section_name)
    filled = filled.replace("{{ outline_section }}", outline_text)
    filled = filled.replace("{{ running_context }}", context_text)
    filled = filled.replace("{{ few_shot_examples }}", fewshot_text)
    filled = filled.replace("{{ bibliography_hints }}", bib_text)

    # 8. Build assembled prompt.
    total = _estimate_tokens(filled)
    budget_report["total"] = total

    return AssembledPrompt(
        system_prompt="",
        user_prompt=filled,
        total_tokens=total,
        budget_report=budget_report,
    )
