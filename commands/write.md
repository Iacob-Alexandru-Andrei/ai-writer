---
description: "Start a new writing session"
argument-hint: "<content-type> <instruction> [--refs <dir>] [--bib <file>] [--examples <a,b>]"
---

Parse `$ARGUMENTS`: first word is **content type** (paper/thesis/blog/linkedin/twitter), rest is **instruction**. Optional flags: `--refs` (corpus dir), `--bib` (bibliography file), `--examples` (comma-separated filenames).

### 1. Start session

```bash
source $HOME/.claude/lib/launcher.sh && claude_run_python '
import json; from pathlib import Path
from writing.pipeline import Pipeline; from writing.models import ContentType
p = Pipeline()
s = p.start_session(content_type=ContentType("<TYPE>"), instruction="<INSTRUCTION>",
    corpus_dir=Path("<REFS>") if "<REFS>" else None,
    bibliography_path=Path("<BIB>") if "<BIB>" else None,
    example_files="<EXAMPLES>".split(",") if "<EXAMPLES>" else None)
print(json.dumps({"session_id": s.session_id, "status": s.status.value, "type": s.content_type.value}, indent=2))
'
```

Replace placeholders with parsed values. Pass `None` for omitted optional args.

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
