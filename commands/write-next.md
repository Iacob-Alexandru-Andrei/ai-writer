---
description: "Continue writing the next section"
argument-hint: "[session-id]"
---

Advance the writing session to the next section. `$ARGUMENTS` is an optional session ID; if omitted, use the most recent session.

### 1. Load session

```bash
source $HOME/.claude/lib/launcher.sh && claude_run_python '
import json; from writing.pipeline import Pipeline; from writing.session import SessionManager
p = Pipeline(); sid = "<SESSION_ID>"
s = p.resume_session(sid) if sid else SessionManager().get_latest()
if not s: print("ERROR: No active session. Start one with /write."); exit(1)
print(json.dumps(p.get_status(s), indent=2, default=str))
'
```

### 2. Generate next section

```bash
source $HOME/.claude/lib/launcher.sh && claude_run_python '
from writing.pipeline import Pipeline
p = Pipeline(); s = p.resume_session("<SESSION_ID>")
print(p.generate_next(s).content)
'
```

Present the section and ask user to **approve** or **reject with feedback**.

### 3. Handle response

- **Approved**: show progress (sections done / total). If all done, call `p.finalize(session)` and present the final document.
- **Rejected**: collect feedback and regenerate:

```bash
source $HOME/.claude/lib/launcher.sh && claude_run_python '
from writing.pipeline import Pipeline
p = Pipeline(); s = p.resume_session("<SESSION_ID>")
print(p.regenerate(s, feedback="<FEEDBACK>").content)
'
```

Present the regenerated section for another review round.
