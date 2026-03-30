---
description: "Start a new writing session"
argument-hint: "<content-type> <instruction> [--refs <dir>] [--bib <file>] [--examples <a,b>] [--llm key=value ...]"
---

Parse `$ARGUMENTS`: first word is **content type** (paper/thesis/blog/linkedin/twitter), rest is **instruction**. Optional flags: `--refs` (corpus dir), `--bib` (bibliography file), `--examples` (comma-separated filenames), `--llm` (repeatable key=value pairs for LLM config: `provider`, `model`, `style_model`, `outline_model`, `section_model`, `context_length`, `max_output_tokens`).

### 1. Start session

```bash
source $HOME/.claude/lib/launcher.sh && claude_run_python '
import json; from pathlib import Path
from writing.pipeline import Pipeline; from writing.models import ContentType
llm_overrides = {k: v for k, v in [x.split("=", 1) for x in "<LLM_OVERRIDES>".split(",") if "=" in x]} if "<LLM_OVERRIDES>" else None
p = Pipeline(llm_overrides=llm_overrides)
s = p.start_session(content_type=ContentType("<TYPE>"), instruction="<INSTRUCTION>",
    corpus_dir=Path("<REFS>") if "<REFS>" else None,
    bibliography_path=Path("<BIB>") if "<BIB>" else None,
    example_files="<EXAMPLES>".split(",") if "<EXAMPLES>" else None)
print(json.dumps({"session_id": s.session_id, "status": s.status.value, "type": s.content_type.value}, indent=2))
'
```

Replace placeholders with parsed values. Pass `None` for omitted optional args. `<LLM_OVERRIDES>` is a comma-joined string of `key=value` pairs from all `--llm` flags (e.g., `provider=codex,model=gpt-5.4`). Pass `None` if no `--llm` flags.

### 2. Outline (long-form only: paper/thesis/blog)

```bash
source $HOME/.claude/lib/launcher.sh && claude_run_python '
import json; from writing.pipeline import Pipeline
p = Pipeline(); s = p.resume_session("<SESSION_ID>")
print(json.dumps(p.generate_outline(s), indent=2))
'
```

Show the outline and style profile summary. Ask user to **approve** or **request changes**.

### 3. Generate first section (after approval, or directly for short-form)

```bash
source $HOME/.claude/lib/launcher.sh && claude_run_python '
from writing.pipeline import Pipeline
p = Pipeline(); s = p.resume_session("<SESSION_ID>")
print(p.generate_next(s).content)
'
```

Present the generated section for review. For short-form content, skip step 2.
