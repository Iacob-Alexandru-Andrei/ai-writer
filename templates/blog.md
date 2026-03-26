# Blog Post Generation

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
- Open with a compelling hook that draws the reader in within the first two sentences.
- Write in an accessible, conversational tone that matches the style profile.
- Target 1500-2500 words for the full post.
- Use subheadings, short paragraphs, and bullet points to improve scannability.
- Include a clear takeaway or call-to-action in the conclusion.

## SEO Guidance
- Weave the primary topic naturally into the opening paragraph.
- Use descriptive subheadings that signal content to both readers and search engines.
- Write a meta description (1-2 sentences, under 160 characters) summarising the post.

## Few-Shot Examples
{{ few_shot_examples }}

## Output
Generate the **{{ section_name }}** section in Markdown. Do not include the
section heading — the pipeline adds it. If this is the final section, append
a meta description on a separate line prefixed with `META:`.
