## Overview

The ai-writer project currently uses a single LLM backend (`ClaudeCLIBackend` calling `claude -p`) for all pipeline stages. This spec adds full backend configurability so that:

- Both Claude (via `claude -p --model`) and Codex (via `~/.claude/bin/codex-run`) are available as generation backends.
- Each pipeline stage (style analysis, outline generation, section generation) can use a different model and provider.
- Configuration follows a three-layer precedence: CLI args > environment variables > YAML config.
- The existing burn-pressure routing hook is respected via an `auto` provider mode that reads `/tmp/orch-routing.json`.
- Failed backends automatically fall back to the alternate provider.
- Model parameters (name, context length, max output tokens) are fully configurable and feed into prompt budget calculations.

## Requirements

### R01: LLM Configuration Types
Create `lib/writing/llm_config.py` with Pydantic models: `Provider` enum (`claude`, `codex`, `auto`), `StageType` enum (`style_analysis`, `outline`, `section_generation`, `default`), `ModelSpec` (provider, model_name, context_length, max_output_tokens), and `LLMSettings` containing per-stage `ModelSpec` fields plus a `default` fallback.

### R02: CodexBackend Implementation
Add `CodexBackend` to `backends.py` that shells out to `~/.claude/bin/codex-run <output_file> exec --full-auto "<prompt>"` with subprocess timeout of 7200 seconds (2 hours). It reads the output file synchronously and returns the content. System prompts are prepended to the user prompt body since Codex CLI has no `--system-prompt` flag. The backend accepts `model_name` and passes it via `-m` flag if set.

### R03: ClaudeCLIBackend Model Selection
Extend `ClaudeCLIBackend` to accept `model_name`, `context_length`, and `max_output_tokens` at construction time. When set, `model_name` is passed via `--model` to `claude -p`. Max output tokens are passed via `--max-tokens` if the CLI supports it, otherwise enforced via prompt instruction.

### R04: FallbackBackend Wrapper
Add `FallbackBackend(primary: LLMBackend, secondary: LLMBackend)` that tries the primary backend and, on transport/runtime/timeout failures only (not content validation), retries with the secondary. Logs the fallback event.

### R05: Auto Provider and Burn-Pressure Integration
When provider is `auto`, `resolve_backend()` reads `/tmp/orch-routing.json` to determine the current primary provider. If the file is missing or malformed, default to `claude` provider. The routing file is read fresh on each stage call so live credit changes are respected mid-session.

### R06: Per-Stage Backend Resolution
Add `resolve_backend(stage: StageType, settings: LLMSettings) -> LLMBackend` factory function that looks up the stage-specific `ModelSpec`, falling back to `default` if the stage has no override. Constructs the appropriate backend (Claude or Codex) wrapped in `FallbackBackend`.

### R07: Three-Layer Config Precedence
Extend `load_settings()` to deep-merge LLM config from three sources with precedence: CLI args (passed as `--llm key=value` pairs) > environment variables (`WRITER_PROVIDER`, `WRITER_MODEL`, `WRITER_STYLE_MODEL`, `WRITER_OUTLINE_MODEL`, `WRITER_SECTION_MODEL`) > YAML (`config/settings.yaml` under a `model:` key). Stage-specific env vars override global ones.

### R08: Pipeline Per-Stage Backend Wiring
Modify `Pipeline.__init__` to accept optional `llm_overrides: dict[str, str] | None` (from CLI `--llm` flags). Resolve per-stage backends and pass them to workflows. `LongFormWorkflow` and `ShortFormWorkflow` store a `dict[StageType, LLMBackend]` instead of a single `_backend`. Each workflow method uses the appropriate stage backend.

### R09: Session LLM Snapshot Persistence
Store the resolved `LLMSettings` in `SessionState` so that `/write-next` resumes with the exact same model configuration. On resume, the stored config is used as the YAML layer, with env and CLI still able to override (allowing intentional mid-session changes).

### R10: Prompt Budget Integration
In `prompt_assembler.py`, use `context_length` and `max_output_tokens` from the active `ModelSpec` to compute the actual token budget for prompt assembly, replacing the current hardcoded estimates. The available prompt budget is `context_length - max_output_tokens - overhead`.

### R11: Outline Engine Selection
Add `outline_engine` config (`llm`, `storm`, `auto`) to prevent STORM from silently bypassing the outline model config. Default to `auto` (STORM if available, else LLM). When set to `llm`, always use the configured outline backend.

### R12: YAML Config Schema
Add default model config to `config/settings.yaml`:
```yaml
model:
  default:
    provider: auto
  style_analysis:
    provider: claude
    model_name: haiku
  outline:
    provider: auto
  section_generation:
    provider: auto
    model_name: opus-4.6
    max_output_tokens: 16384
    context_length: 200000
  outline_engine: auto
```

### R13: Slash Command Updates
Update `commands/write.md` to accept `--llm key=value` pairs (e.g., `--llm provider=codex --llm model=opus-4.6 --llm section_model=opus-4.6`). Update `commands/write-next.md` to use the session's stored LLM config by default.

### R14: Backward Compatibility
`Pipeline(backend=some_backend)` continues to work for tests and direct use — it bypasses per-stage resolution and uses the provided backend for all stages. All existing tests pass without modification.

## Dual-Plan Synthesis

### Agreements
- New per-stage config types (`ModelSpec`, `LLMSettings`, `StageType`, `Provider`) as Pydantic models
- `CodexBackend` wrapping `codex-run`, synchronous-blocking, output-file based
- `FallbackBackend` wrapper with primary/secondary pattern
- Per-stage backend resolution in pipeline
- Three-layer config precedence (CLI > env > YAML) resolved at session start
- Session persistence of resolved LLM config for reproducible resume
- STORM outline bypass needs explicit `outline_engine` control
- Backward compatibility for `Pipeline(backend=mock)` in tests

### Divergences
- **Config types location**: Codex proposed `llm_config.py`; Claude proposed additions to `models.py`. Chose `llm_config.py` — cleaner domain boundary, keeps `models.py` focused on content/session types.
- **CLI flag format**: Codex proposed `--llm key=value`; Claude proposed `--model`/`--provider` flags. Chose `--llm key=value` — more extensible, avoids flag explosion as new params are added.
- **Routing reads**: Both read `/tmp/orch-routing.json`, but Codex reads fresh per-stage call. Chose per-stage reads — respects live credit changes during long paper sessions.
- **Fallback scope**: Codex limits fallback to transport/runtime failures; Claude catches all exceptions. Chose Codex approach — validation failures are the caller's responsibility, not fallback triggers.
- **System prompt in Codex**: Codex plan correctly identified that Codex CLI lacks `--system-prompt`; system must be prepended to prompt body. Adopted.

## Technical Approach

### Architecture

```
CLI args (--llm k=v)
        |
        v
+------------------+
| load_settings()  | <- merges CLI > env > YAML
| -> LLMSettings   |
+--------+---------+
         |
         v
+----------------------+
| resolve_backend()    | <- per stage, reads /tmp/orch-routing.json for "auto"
| -> FallbackBackend   |
|   +- primary: Claude | or Codex (based on routing)
|   +- secondary: Codex| or Claude (the other one)
+--------+-------------+
         |
    +----+-----+
    | Pipeline  |
    | +- style_analysis_backend
    | +- outline_backend
    | +- section_backend
    +----------+
```

### Key Decisions
1. **Synchronous Codex**: `CodexBackend.generate()` blocks until `codex-run` completes (up to 2h). This is correct for section generation (sequential dependency). The orchestrator handles parallelism at a higher level if needed.
2. **Fresh routing reads**: Each `resolve_backend()` call reads the routing file anew. If credits shift mid-paper, later sections may use a different provider. The session snapshot stores the config (not the resolved provider), preserving this flexibility.
3. **Codex timeout**: 7200s (2 hours) per CLAUDE.md constraint. Quality over speed.
4. **Burn-pressure hook integration**: The existing `pre-agent-codex-nudge.sh` hook enforces routing at the orchestrator level. The ai-writer's `auto` provider reads the same routing file as a cooperative hint, not as a competing authority.

## Edge Cases & Error Handling

- **Missing routing file**: `/tmp/orch-routing.json` absent -> default to `claude` provider. Log warning.
- **Malformed routing file**: JSON parse error -> default to `claude`. Log warning.
- **Codex output empty**: `codex-run` produces empty output file -> raise `RuntimeError`, triggers fallback to Claude.
- **Both backends fail**: `FallbackBackend` raises the secondary's exception with context that primary also failed.
- **Unknown model name**: Pass through to the CLI — let `claude -p` or `codex-run` validate and error.
- **Session resume with changed env**: Stored LLM config provides the base; env/CLI can still override intentionally.
- **STORM + outline model conflict**: When `outline_engine=storm`, the outline model config is ignored (STORM has its own model). When `outline_engine=llm`, STORM is bypassed entirely.
- **Codex subprocess killed**: Handle `subprocess.TimeoutExpired` and `CalledProcessError` as fallback-triggering failures.

## Acceptance Criteria

### AC01: Codex Backend Works
A paper session started with `provider=codex` uses `codex-run` for generation and produces valid section output. Verified by checking subprocess call args in test.

### AC02: Claude Model Selection Works
A paper session started with `model_name=opus-4.6` passes `--model opus-4.6` to `claude -p`. Verified by inspecting the constructed command.

### AC03: Per-Stage Configuration
Starting a session with `style_analysis.model_name=haiku` and `section_generation.model_name=opus-4.6` results in different backends being called for each stage. Verified by mock injection per stage.

### AC04: Config Precedence
CLI `--llm provider=codex` overrides env `WRITER_PROVIDER=claude` which overrides YAML `provider: auto`. Verified by unit test with all three layers set.

### AC05: Fallback on Failure
When the primary backend (e.g., Codex) fails with a subprocess error, the system automatically retries with the secondary (Claude) and succeeds. Verified by mock that raises on first call.

### AC06: Session Persistence
A session started with specific LLM config, when resumed via `Pipeline.resume_session()`, uses the same model configuration without re-specifying CLI args. Verified by round-trip save/load.

### AC07: Routing Integration
With `provider=auto` and `/tmp/orch-routing.json` indicating `codex` as primary, the system uses `CodexBackend`. With the file missing, it defaults to Claude. Verified by writing/removing the routing file in test.

### AC08: Prompt Budget Integration
Setting `context_length=200000` and `max_output_tokens=16384` results in `assemble_prompt()` using `200000 - 16384 - overhead` as the token budget. Verified by assertion on `AssembledPrompt.total_tokens`.

### AC09: Backward Compatibility
All existing tests pass unchanged. `Pipeline(backend=mock_backend)` uses the mock for all stages. Verified by running the existing test suite.

### AC10: Outline Engine Control
Setting `outline_engine=llm` bypasses STORM even when STORM is available, and uses the configured outline backend. Verified by mock that asserts STORM adapter is never called.
