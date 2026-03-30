<!-- autonomy:active -->
<!-- failures:0 -->
<!-- generated:2026-03-30T14:10:00Z -->
<!-- spec:SPEC.md -->
<!-- task-count:13 -->
<!-- dispatches:0 -->
<!-- elapsed-s:0 -->
<!-- convergence:0 -->
<!-- planned:dual-plan -->

# TASKS

Generated from SPEC.md. 13 tasks.

- [ ] T01: Create LLM configuration types and YAML schema
  - Ref: R01, R07, R12
  - Type: substantive
  - Route: codex
  - Goal: Create `lib/writing/llm_config.py` with Provider enum (claude/codex/auto), StageType enum (style_analysis/outline/section_generation/default), ModelSpec (provider, model_name, context_length, max_output_tokens), LLMSettings (per-stage ModelSpec fields + default fallback + outline_engine). Add `model:` section to `config/settings.yaml` with defaults: claude default model `opus-4.6`, codex default model `gpt-5.4`. Extend `load_settings()` in `settings.py` to load the `model:` YAML key into `LLMSettings`, parse env vars (`WRITER_PROVIDER`, `WRITER_MODEL`, `WRITER_STYLE_MODEL`, `WRITER_OUTLINE_MODEL`, `WRITER_SECTION_MODEL`), accept CLI overrides dict, and deep-merge with precedence CLI > env > YAML. All backends use CLI tools (claude -p, codex-run), never API.
  - Acceptance: AC04 — `load_settings(llm_overrides={"provider": "codex"})` overrides env `WRITER_PROVIDER=claude` which overrides YAML `provider: auto`. Unit tests verify all three layers and deep-merge.
  - Files: lib/writing/llm_config.py (new), lib/writing/settings.py, config/settings.yaml
  - Depends: none
  - Parallel: none
  - [ ] Dispatched (→ TaskOutput block:true to collect result; if using worktrees, agents must checkout the feature branch)
  - [ ] Validated (→ run-validation.sh + python -c "from writing.llm_config import Provider, StageType, ModelSpec, LLMSettings")
  - [ ] Committed (→ git commit + push)

- [ ] T02: Implement all backend classes (Claude model selection, Codex, Fallback, routing, resolver)
  - Ref: R02, R03, R04, R05, R06
  - Type: substantive
  - Route: codex
  - Goal: In `backends.py`: (1) Extend `ClaudeCLIBackend.__init__` to accept `model_name`, `context_length`, `max_output_tokens`; pass `--model` to `claude -p` when set. (2) Add `CodexBackend` that shells to `~/.claude/bin/codex-run <output_file> exec --full-auto "<prompt>"` with subprocess timeout 7200s; reads output file; prepends system prompt to user prompt body; passes model via `-m` if set; default model `gpt-5.4`. (3) Add `FallbackBackend(primary, secondary)` that catches subprocess/timeout/runtime errors only (not content validation) and retries with secondary; logs fallback. (4) Add `read_routing_state()` that reads `/tmp/orch-routing.json`, returns primary provider or defaults to `claude` on missing/malformed. (5) Add `resolve_backend(stage, settings)` factory that looks up stage-specific ModelSpec (falling back to default), reads routing for `auto` provider, constructs Claude or Codex backend, wraps in FallbackBackend. Resolution must be callable per-stage (not eagerly cached) so `auto` reads routing fresh each time.
  - Acceptance: AC01 — CodexBackend constructs correct codex-run command. AC02 — ClaudeCLIBackend passes --model. AC05 — FallbackBackend retries on subprocess error. AC07 — auto provider reads routing file.
  - Files: lib/writing/backends.py
  - Depends: T01
  - Parallel: none
  - [ ] Dispatched (→ TaskOutput block:true to collect result; if using worktrees, agents must checkout the feature branch)
  - [ ] Validated (→ run-validation.sh + python -c "from writing.backends import CodexBackend, FallbackBackend, resolve_backend")
  - [ ] Committed (→ git commit + push)

- [ ] T03: Write tests for T01 and T02
  - Ref: R01, R02, R03, R04, R05, R06, R07, R12
  - Type: substantive
  - Route: codex
  - Goal: Add `tests/test_llm_config.py` testing ModelSpec/LLMSettings creation and validation. Add `tests/test_backends_config.py` testing: ClaudeCLIBackend command construction with --model flag, CodexBackend command construction and output file reading (mock subprocess), FallbackBackend primary-fail-secondary-succeed and both-fail, read_routing_state with present/missing/malformed file, resolve_backend with explicit providers and auto mode. Add `tests/test_settings_llm.py` testing three-layer config precedence (mock env vars, yaml, cli overrides).
  - Acceptance: AC04, AC05, AC07 — all tests pass via `pytest tests/test_llm_config.py tests/test_backends_config.py tests/test_settings_llm.py -v`
  - Files: tests/test_llm_config.py (new), tests/test_backends_config.py (new), tests/test_settings_llm.py (new)
  - Depends: T01, T02
  - Parallel: none
  - [ ] Dispatched (→ TaskOutput block:true to collect result; if using worktrees, agents must checkout the feature branch)
  - [ ] Validated (→ run-validation.sh + pytest tests/test_llm_config.py tests/test_backends_config.py tests/test_settings_llm.py -v)
  - [ ] Committed (→ git commit + push)

- [ ] T04: Milestone — push and review foundation
  - Ref: R01, R02, R03, R04, R05, R06, R07, R12
  - Type: trivial
  - Route: orchestrator
  - Goal: Push all pending work, verify tests pass, review diffs
  - Acceptance: all prior tasks committed and pushed, pytest passes
  - Files: (git operations)
  - Depends: T01, T02, T03
  - Parallel: none
  - [ ] Committed (→ git commit + push)
  - [ ] PR reviews (→ /pr-review-reactor sync; inject fix tasks if needed)

- [ ] T05: Wire per-stage backends into Pipeline and workflows
  - Ref: R08, R14
  - Type: substantive
  - Route: codex
  - Goal: Modify `Pipeline.__init__` to accept optional `llm_overrides: dict[str, str] | None`. When `backend` kwarg is provided (backward compat), use it for all stages and skip resolution. Otherwise, call `resolve_backend()` lazily per-stage (not eagerly at init). Modify `LongFormWorkflow` to accept a backend resolver callable instead of a single backend; `start()` calls resolver with `style_analysis`, `generate_outline()` with `outline`, `generate_section()` with `section_generation`. Same pattern for `ShortFormWorkflow`. Existing `Pipeline(backend=mock)` path must still work unchanged.
  - Acceptance: AC03 — different backends used per stage. AC09 — Pipeline(backend=mock) works for all stages.
  - Files: lib/writing/pipeline.py, lib/writing/workflows/long_form.py, lib/writing/workflows/short_form.py
  - Depends: T02
  - Parallel: none
  - [ ] Dispatched (→ TaskOutput block:true to collect result; if using worktrees, agents must checkout the feature branch)
  - [ ] Validated (→ run-validation.sh + pytest tests/ -v)
  - [ ] Committed (→ git commit + push)

- [ ] T06: Add session LLM snapshot persistence
  - Ref: R09
  - Type: substantive
  - Route: codex
  - Goal: Add `llm_settings: LLMSettings | None = None` field to `SessionState` in `models.py`. Extend `SessionManager.create()` to accept and store it. On `Pipeline.start_session()`, store the resolved LLMSettings in the session. On `Pipeline.resume_session()`, load stored LLMSettings and use it as the base config layer (env/CLI can still override). Handle `/write-next` flow where Pipeline() is constructed before resume — the resume must rebind backends from stored snapshot.
  - Acceptance: AC06 — round-trip save/load preserves LLM config
  - Files: lib/writing/models.py, lib/writing/session.py, lib/writing/pipeline.py
  - Depends: T05
  - Parallel: T07
  - [ ] Dispatched (→ TaskOutput block:true to collect result; if using worktrees, agents must checkout the feature branch)
  - [ ] Validated (→ run-validation.sh + python -c "from writing.models import SessionState; s = SessionState(content_type='paper', instruction='test'); assert hasattr(s, 'llm_settings')")
  - [ ] Committed (→ git commit + push)

- [ ] T07: Integrate prompt budget from ModelSpec
  - Ref: R10
  - Type: substantive
  - Route: codex
  - Goal: Modify `assemble_prompt()` in `prompt_assembler.py` to accept optional `context_length` and `max_output_tokens` parameters. When provided, compute available prompt budget as `context_length - max_output_tokens - overhead` and use it to cap the total prompt size. Update `LongFormWorkflow.generate_section()` and `ShortFormWorkflow._build_prompt()` to pass the active ModelSpec's context_length and max_output_tokens to `assemble_prompt()`.
  - Acceptance: AC08 — setting context_length=200000 and max_output_tokens=16384 results in prompt assembly using those limits
  - Files: lib/writing/prompt_assembler.py, lib/writing/workflows/long_form.py, lib/writing/workflows/short_form.py
  - Depends: T05
  - Parallel: T06
  - [ ] Dispatched (→ TaskOutput block:true to collect result; if using worktrees, agents must checkout the feature branch)
  - [ ] Validated (→ run-validation.sh + pytest tests/ -v)
  - [ ] Committed (→ git commit + push)

- [ ] T08: Add outline engine selection
  - Ref: R11
  - Type: substantive
  - Route: codex
  - Goal: Add `outline_engine` field (enum: `llm`, `storm`, `auto`) to `LLMSettings`. In `LongFormWorkflow.generate_outline()`, check `outline_engine`: if `llm`, bypass STORM entirely and use configured outline backend; if `storm`, use STORM (ignore outline model config); if `auto`, try STORM first, fall back to LLM (current behavior). Pass outline_engine through from session's LLMSettings.
  - Acceptance: AC10 — setting outline_engine=llm bypasses STORM even when available
  - Files: lib/writing/llm_config.py, lib/writing/workflows/long_form.py
  - Depends: T05
  - Parallel: T06, T07
  - [ ] Dispatched (→ TaskOutput block:true to collect result; if using worktrees, agents must checkout the feature branch)
  - [ ] Validated (→ run-validation.sh + pytest tests/ -v)
  - [ ] Committed (→ git commit + push)

- [ ] T09: Milestone — push and review pipeline wiring
  - Ref: R08, R09, R10, R11, R14
  - Type: trivial
  - Route: orchestrator
  - Goal: Push all pending work, verify all tests pass, review diffs
  - Acceptance: all prior tasks committed and pushed, pytest passes
  - Files: (git operations)
  - Depends: T05, T06, T07, T08
  - Parallel: none
  - [ ] Committed (→ git commit + push)
  - [ ] PR reviews (→ /pr-review-reactor sync; inject fix tasks if needed)

- [ ] T10: Update slash commands for --llm flag
  - Ref: R13
  - Type: trivial
  - Route: orchestrator
  - Goal: Update `commands/write.md` to parse `--llm key=value` pairs from $ARGUMENTS and pass them as `llm_overrides` dict to `Pipeline.start_session()`. Update `commands/write-next.md` to load session's stored LLM config automatically; accept optional `--llm` overrides for intentional mid-session changes.
  - Acceptance: `/write paper "topic" --refs ./corpus --llm provider=codex --llm model=gpt-5.4` passes overrides correctly
  - Files: commands/write.md, commands/write-next.md
  - Depends: T06
  - Parallel: none
  - [ ] Dispatched (→ TaskOutput block:true to collect result; if using worktrees, agents must checkout the feature branch)
  - [ ] Validated (→ run-validation.sh)
  - [ ] Committed (→ git commit + push)

- [ ] T11: Write integration and pipeline wiring tests
  - Ref: R08, R09, R10, R11, R14
  - Type: substantive
  - Route: codex
  - Goal: Add tests verifying: (1) Pipeline with per-stage mock backends calls correct backend per stage (style_analysis vs section_generation). (2) Session round-trip preserves LLM config and resume uses stored config. (3) Pipeline(backend=mock) backward compat — all stages use the mock. (4) Prompt budget integration with custom context_length/max_output_tokens. (5) Outline engine=llm bypasses STORM. (6) All existing tests still pass.
  - Acceptance: AC03, AC06, AC08, AC09, AC10 — all tests pass
  - Files: tests/test_pipeline_backends.py (new), tests/integration/test_full_workflow.py
  - Depends: T05, T06, T07, T08
  - Parallel: T10
  - [ ] Dispatched (→ TaskOutput block:true to collect result; if using worktrees, agents must checkout the feature branch)
  - [ ] Validated (→ run-validation.sh + pytest tests/ -v)
  - [ ] Committed (→ git commit + push)

- [ ] T12: Spec coverage audit and final CI validation
  - Ref: R01-R14
  - Type: substantive
  - Route: orchestrator
  - Goal: Verify every requirement R01-R14 is implemented. Verify every acceptance criterion AC01-AC10 has a passing test. Run full test suite 3 times. Fix any remaining issues.
  - Acceptance: all AC01-AC10 verified, pytest passes 3/3 runs
  - Files: (review only, fix if needed)
  - Depends: T10, T11
  - Parallel: none
  - [ ] Dispatched (→ TaskOutput block:true to collect result; if using worktrees, agents must checkout the feature branch)
  - [ ] Validated (→ run-validation.sh + pytest tests/ -v (3 runs))
  - [ ] Committed (→ git commit + push)

- [ ] T13: Final sign-off
  - Ref: R01-R14
  - Type: trivial
  - Route: orchestrator
  - Goal: Final push, verify clean git state, confirm all tasks complete
  - Acceptance: git status clean, all tasks checked, pytest green
  - Files: (git operations)
  - Depends: T12
  - Parallel: none
  - [ ] Committed (→ git commit + push)

## Follow-Up Ideas

### In-Scope
- R10: Add token counting via tiktoken for more accurate budget enforcement
- R02: Add Codex output streaming/progress for long-running section generation

### Novel / Orthogonal
- Multi-model ensemble: generate sections with both Claude and Codex, pick the best
- Cost tracking: log API/CLI costs per session for budget awareness
- Model quality benchmarking: A/B test different models on same section for quality comparison
