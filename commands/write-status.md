---
description: "Show current writing session status"
argument-hint: "[session-id]"
---

Display the state of a writing session. `$ARGUMENTS` is an optional session ID; if omitted, use the most recent session.

### 1. Load and display status

```bash
source $HOME/.claude/lib/launcher.sh && claude_run_python '
import json; from writing.pipeline import Pipeline; from writing.session import SessionManager
p = Pipeline(); sid = "<SESSION_ID>"
s = p.resume_session(sid) if sid else SessionManager().get_latest()
if not s: print("ERROR: No active session found."); exit(1)
print(json.dumps({
    "session_id": s.session_id, "content_type": s.content_type.value,
    "status": s.status.value, "instruction": s.instruction,
    "sections_completed": len(s.sections),
    "sections_total": len(s.outline) if s.outline else "N/A",
    "outline": s.outline or "No outline (short-form)"
}, indent=2, default=str))
'
```

### 2. Present clearly

- **Session ID**: unique identifier
- **Content type**: paper / thesis / blog / linkedin / twitter
- **Status**: analyzing / outlining / generating / reviewing / complete
- **Instruction**: the original writing prompt
- **Progress**: sections completed out of total
- **Outline**: numbered section titles (long-form only)

If no session exists, suggest running `/write` to start one.
