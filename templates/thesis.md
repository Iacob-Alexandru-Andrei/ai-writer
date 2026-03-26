# Thesis Chapter Generation

## Style Profile
{{ style_profile }}

## Instruction
{{ instruction }}

## Current Chapter / Section: {{ section_name }}

### Chapter Context
{{ chapter_context }}

### Outline Context
{{ outline_section }}

### Running Context
{{ running_context }}

## Guidelines
- Write in a formal academic tone suitable for a graduate-level thesis.
- Each chapter should build on prior chapters as summarised in the running context.
- Provide thorough literature engagement where applicable.
- Use transitional paragraphs to connect sub-sections within the chapter.
- Maintain consistent notation and terminology throughout.

## Few-Shot Examples
{{ few_shot_examples }}

## Bibliography Hints
{{ bibliography_hints }}

## Output
Generate the content for **{{ section_name }}**. Do not include the chapter
or section heading — headings are managed by the pipeline. Use square-bracket
citation keys (e.g., [AuthorYear]) that match the bibliography hints.
