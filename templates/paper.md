# Academic Paper Generation

## Style Profile
{{ style_profile }}

## Instruction
{{ instruction }}

## Current Section: {{ section_name }}

### Outline Context
{{ outline_section }}

### Running Context
{{ running_context }}

## Guidelines
- Write in a formal academic tone consistent with the style profile above.
- Maintain logical flow from preceding sections captured in the running context.
- Support claims with evidence and cite sources using the bibliography hints.
- Use precise, domain-specific vocabulary appropriate to the field.
- Structure paragraphs with clear topic sentences and supporting details.

## Few-Shot Examples
{{ few_shot_examples }}

## Bibliography Hints
{{ bibliography_hints }}

## Output
Generate the **{{ section_name }}** section in Markdown. Do not include the
section heading itself — the pipeline adds headings automatically. Embed
citations in square-bracket notation (e.g., [AuthorYear]) matching the
bibliography keys provided.
